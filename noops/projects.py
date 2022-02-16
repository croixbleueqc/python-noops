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
from .typing.projectplans import ProjectPlanKind, ProjectPlanSpec
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

            spec: ProjectKindSpec = kproject.spec.copy(deep=True)
            spec.versions = kversion.spec.copy(deep=True)

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
            metadata = kproject.metadata.copy(deep=True)
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
    def apply(cls, kplan: ProjectPlanKind, pre_processing_path: Path, dry_run: bool,
        kpreviousplan: ProjectPlanKind = None):
        """
        Apply the plan
        """

        # TODO: Implement diff between 2 ProjectPlanKind and run the reconciliation.
        #       Can use apply_incluster and delete_incluster with HelmInstall(dry_run, cluster) ?

        for plan in kplan.spec.plan:
            kproject = ProjectKind(spec=plan.template.spec, metadata=kplan.metadata)
            for cluster in plan.clusters:
                logging.info(
                    "apply project %s.%s in cluster %s.",
                    kplan.metadata.name,
                    kplan.metadata.namespace,
                    cluster
                )

        raise NotImplementedError()

    @classmethod
    def apply_incluster(cls, kproject: ProjectKind, pre_processing_path: Path, dry_run: bool,
        kprevious: ProjectKind = None):
        """
        Install the project in cluster
        """
        if kprevious is None:
            # We need an empty from for reconciliation
            kprevious = cls.create_skeleton_from(kproject)

        HelmInstall(dry_run).reconciliation(kproject, kprevious, pre_processing_path)

    @classmethod
    def delete_incluster(cls, kproject: ProjectKind, dry_run: bool):
        """
        Delete everything controlled by this project
        """
        kempty = cls.create_skeleton_from(kproject)

        # kempty is the target as we want to remove all versions previously installed.
        HelmInstall(dry_run).reconciliation(kempty, kproject)
