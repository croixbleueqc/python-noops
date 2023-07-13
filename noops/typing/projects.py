"""
Projects Typing
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

from typing import Literal, Optional, List, Union
from pydantic import BaseModel, Field # pylint: disable=no-name-in-module
from .versions import OneSpec, MultiSpec, Spec as VersionSpec
from .metadata import MetadataSpec
from .targets import TargetsEnum

class ProjectReconciliationPlan(BaseModel): # pylint: disable=too-few-public-methods
    """Plan to reconcile an older project with a new one"""
    added: List[Union[OneSpec, MultiSpec]] = []
    changed: List[Union[OneSpec, MultiSpec]] = []
    removed: List[Union[OneSpec, MultiSpec]] = []

    canary_versions: Optional[List[Union[OneSpec, MultiSpec]]]
    removed_canary: bool = False

class WhiteLabelSpec(BaseModel): # pylint: disable=too-few-public-methods
    """package white-label spec"""
    rebrand: str
    marketer: str

class InstallSpec(BaseModel): # pylint: disable=too-few-public-methods
    """package install spec"""
    chart: str
    env: str
    target: Optional[TargetsEnum]
    services_only: bool = Field(False, alias='services-only')
    args: Optional[List[str]]
    envs: Optional[dict]
    white_label: Optional[WhiteLabelSpec] = Field(None, alias='white-label')

class PackageSpec(BaseModel): # pylint: disable=too-few-public-methods
    """package spec"""
    install: InstallSpec

class Spec(BaseModel): # pylint: disable=too-few-public-methods
    """kind spec model"""
    package: PackageSpec
    versions: VersionSpec = VersionSpec(one=None, multi=None)

class ProjectKind(BaseModel): # pylint: disable=too-few-public-methods
    """Project Kind model"""
    apiVersion: Literal['noops.local/v1alpha1'] = 'noops.local/v1alpha1'
    kind: Literal['Project'] = 'Project'
    spec: Spec
    metadata: MetadataSpec
