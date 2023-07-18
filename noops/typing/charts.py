"""
Charts Typing
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

from typing import Optional, List, Literal
from pydantic import BaseModel, Field # pylint: disable=no-name-in-module
from .targets import TargetClasses
from .profiles import ProfileClasses

class SupportedSpec(BaseModel): # pylint: disable=too-few-public-methods
    """
    Supported model
    """
    profile_classes: ProfileClasses = Field(..., alias="profile-classes")
    target_classes: TargetClasses = Field(..., alias='target-classes')

class HelmSpec(BaseModel): # pylint: disable=too-few-public-methods
    """
    Helm model
    """
    preprocessing: List[str] = Field([], alias='pre-processing')

class PackageSpec(BaseModel): # pylint: disable=too-few-public-methods
    """
    Package model
    """
    helm: HelmSpec
    supported: Optional[SupportedSpec] = None

class Spec(BaseModel): # pylint: disable=too-few-public-methods
    """
    Specification model
    """
    package: PackageSpec

class ChartKind(BaseModel): # pylint: disable=too-few-public-methods
    """Chart Kind model"""
    apiVersion: Literal['noops.local/v1alpha1'] = 'noops.local/v1alpha1'
    kind: Literal['Chart'] = 'Chart'
    spec: Spec
