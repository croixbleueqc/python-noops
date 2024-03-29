"""
Projects Plan Typing
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

from typing import Literal, List, Optional
from pydantic import BaseModel, Field # pylint: disable=no-name-in-module
from .projects import Spec as ProjectsSpec, ProjectKind
from .targets import TargetClassesEnum
from .metadata import MetadataSpec

class ProjectPlanReconciliation(BaseModel):
    """Reconciliation per cluster"""
    cluster: str
    kproject: Optional[ProjectKind] = None
    kprevious: Optional[ProjectKind] = None

    def is_apply(self) -> bool:
        """Do we have to install or upgrade the project ?"""
        return self.kproject is not None

    def is_delete(self) -> bool:
        """Do we have to remove the project ?"""
        return self.kproject is None and self.kprevious is not None

class TemplateSpec(BaseModel): # pylint: disable=too-few-public-methods
    """Template spec model"""
    spec: ProjectsSpec

class ProjectPlanSpec(BaseModel): # pylint: disable=too-few-public-methods
    """Project plan spec model"""
    clusters: List[str] = []
    template: TemplateSpec

class Spec(BaseModel): # pylint: disable=too-few-public-methods
    """kind spec model"""
    target_class: TargetClassesEnum = Field(..., alias="target-class")
    plan: List[ProjectPlanSpec] = []

class ProjectPlanKind(BaseModel): # pylint: disable=too-few-public-methods
    """Project Kind model"""
    apiVersion: Literal['noops.local/v1alpha1'] = 'noops.local/v1alpha1'
    kind: Literal['ProjectPlan'] = 'ProjectPlan'
    spec: Spec
    metadata: MetadataSpec
