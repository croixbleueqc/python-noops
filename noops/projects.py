"""
NoOps Package

To handle package.noops.local/v1alpha1
"""

# Copyright 2021 Croix Bleue du Québec

# This file is part of python-noops.

# python-noops is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# python-noops is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with python-noops.  If not, see <https://www.gnu.org/licenses/>.

import logging
from typing import List
from pathlib import Path
from .typing.targets import Cluster, TargetKind, TargetClassesEnum, TargetsEnum
from .typing.versions import VersionKind
from .typing.projects import ProjectKind, Spec as ProjectKindSpec
from .typing.projectplans import (
    ProjectPlanKind,
    ProjectPlanSpec,
    ProjectPlanReconciliation
)
from .targets import Targets
from .package.install import HelmInstall

class Projects():
    """
    Projects
    """

    @classmethod
    def plan(cls, clusters: List[Cluster],
        ktarget: TargetKind, kversion: VersionKind, kproject: ProjectKind) -> ProjectPlanKind:
        """
        Plan
        """
        # Create target plan (target class, clusters to use...)
        target_plan = Targets(clusters).plan(ktarget)

        # Verify versions
        kversion.verify()

        # Create project plan
        plan = []

        for target_clusters, scope in (
                (target_plan.active, "active"),
                (target_plan.standby, "standby"),
                (target_plan.services_only, "services-only")
            ):
            if len(target_clusters) == 0:
                continue

            spec: ProjectKindSpec = kproject.spec.model_copy(deep=True)
            spec.versions = kversion.spec.model_copy(deep=True)

            if target_plan.target_class == TargetClassesEnum.ONE_CLUSTER:
                spec.package.install.target = TargetsEnum.ONE_CLUSTER
            elif target_plan.target_class == TargetClassesEnum.MULTI_CLUSTER:
                spec.package.install.target = TargetsEnum.MULTI_CLUSTER
            else:
                spec.package.install.target = TargetsEnum(scope)

            spec.package.install.services_only = (scope == "services-only")

            # Add to the plan
            plan.append(
                ProjectPlanSpec(
                    clusters=target_clusters,
                    template={ "spec": spec }
                )
            )

        project_plan = ProjectPlanKind(
            spec = {
                "target-class": target_plan.target_class,
                "plan": plan
            },
            metadata = kproject.metadata.model_copy(deep=True)
        )

        # TODO: Verify NoOps Helm package compatibility involved with the plan

        return project_plan

    @classmethod
    def create(cls, namespace: str, release: str, chart: str, env: str,
        cargs: List[str] = None, extra_envs: dict = None) -> ProjectKind:
        """
        Create a new project
        """
        project = ProjectKind(
            spec={
                "package": {
                    "install": {
                        "chart": chart,
                        "env": env,
                        "args": cargs,
                        "envs": extra_envs
                    }
                }
            },
            metadata={
                "name": release,
                "namespace": namespace
            }
        )

        return project

    @classmethod
    def create_skeleton_from(cls, kproject: ProjectKind) -> ProjectKind:
        """
        Create a project based on an existing one but without any versions set
        """
        return ProjectKind(
            metadata = kproject.metadata,
            spec = {
                "package": {
                    "install": kproject.spec.package.install
                }
            }
        )

    @classmethod
    def _reconciliation_project_plan(cls,
        current: ProjectPlanKind, previous: ProjectPlanKind) -> List[ProjectPlanReconciliation]:
        """
        Determine what need to be changed from previous to current project plan definition
        """

        plans = []

        def populate_per_cluster(projectplan: ProjectPlanKind, per_cluster: dict):
            """Populate a dict with cluster/ProjectKind"""
            for _plan in projectplan.spec.plan:
                for cluster in _plan.clusters:
                    per_cluster[cluster] = \
                        ProjectKind(spec=_plan.template.spec, metadata=projectplan.metadata)

        current_per_cluster = {}
        populate_per_cluster(current, current_per_cluster)
        previous_per_cluster = {}
        populate_per_cluster(previous, previous_per_cluster)

        # install/upgrade
        for cluster, kproject in current_per_cluster.items():
            try:
                kprevious = previous_per_cluster.pop(cluster)
            except KeyError:
                kprevious = None

            plans.append(
                ProjectPlanReconciliation(
                    cluster=cluster,
                    kproject=kproject,
                    kprevious=kprevious
                )
            )

        # uninstall
        for cluster, kprevious in previous_per_cluster.items():
            plans.append(
                ProjectPlanReconciliation(
                    cluster=cluster,
                    kprevious=kprevious
                )
            )

        return plans

    @classmethod
    def apply(cls, kplan: ProjectPlanKind, pre_processing_path: Path, dry_run: bool,
        kpreviousplan: ProjectPlanKind = None):
        """
        Apply the plan
        """

        if kpreviousplan is None:
            kpreviousplan = ProjectPlanKind(
                metadata=kplan.metadata,
                spec={
                    "target-class": kplan.spec.target_class
                }
            )

        plans = cls._reconciliation_project_plan(kplan, kpreviousplan)

        for plan in plans:
            if plan.is_delete():
                cls.delete_incluster(plan.kprevious, dry_run, cluster=plan.cluster)
            elif plan.is_apply():
                cls.apply_incluster(
                    plan.kproject,
                    pre_processing_path,
                    dry_run,
                    kprevious=plan.kprevious,
                    cluster=plan.cluster
                )

    @classmethod
    def apply_incluster(cls, kproject: ProjectKind, pre_processing_path: Path, dry_run: bool,
        kprevious: ProjectKind = None, cluster: str = None):
        """
        Install the project in cluster
        """
        logging.info(
            "applying project %s.%s in cluster %s.",
            kproject.metadata.name,
            kproject.metadata.namespace,
            cluster or ""
        )

        if kprevious is None:
            # We need an empty from for reconciliation
            kprevious = cls.create_skeleton_from(kproject)

        HelmInstall(dry_run, kube_context=cluster) \
            .reconciliation(kproject, kprevious, pre_processing_path)

    @classmethod
    def delete_incluster(cls, kproject: ProjectKind, dry_run: bool, cluster: str = None):
        """
        Delete everything controlled by this project
        """
        logging.info(
            "deleting project %s.%s in cluster %s.",
            kproject.metadata.name,
            kproject.metadata.namespace,
            cluster or ""
        )

        kempty = cls.create_skeleton_from(kproject)

        # kempty is the target as we want to remove all versions previously installed.
        HelmInstall(dry_run, kube_context=cluster) \
            .reconciliation(kempty, kproject)
