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
        ktarget: TargetKind, kversion: VersionKind, kproject: ProjectKind):
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
                if scope == "services-only":
                    spec.package.install.target = None
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
        cargs: List[str] = None, extra_envs: dict = None):
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

        print(project.dict(by_alias=True))

    @classmethod
    def apply(cls, kplan: ProjectPlanKind, pre_processing_path: Path, dry_run: bool):
        """
        Apply the plan

        Connect to each cluster and install the project (install.py)
        """
        for plan in kplan.spec.plan:
            kproject = ProjectKind(spec=plan.template.spec, metadata=kplan.metadata)
            HelmInstall(dry_run).reconciliation(kproject, pre_processing_path)
