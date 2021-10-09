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

from typing import Literal, List
from pydantic import BaseModel, Field # pylint: disable=no-name-in-module
from .projects import Spec as ProjectsSpec
from .targets import TargetClassesEnum

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
    kind: Literal['projectplan'] = 'projectplan'
    spec: Spec
