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

from typing import Literal, Optional, List
from pydantic import BaseModel, Field # pylint: disable=no-name-in-module
from . import versions
from .metadata import MetadataSpec

class InstallSpec(BaseModel): # pylint: disable=too-few-public-methods
    """package install spec"""
    chart: str
    env: str
    target: Optional[str]
    services_only: bool = Field(False, alias='services-only')
    args: Optional[List[str]]
    envs: Optional[dict]

class PackageSpec(BaseModel): # pylint: disable=too-few-public-methods
    """package spec"""
    install: InstallSpec

class Spec(BaseModel): # pylint: disable=too-few-public-methods
    """kind spec model"""
    package: PackageSpec
    versions: Optional[versions.Spec]

class ProjectKind(BaseModel): # pylint: disable=too-few-public-methods
    """Project Kind model"""
    apiVersion: Literal['noops.local/v1alpha1'] = 'noops.local/v1alpha1'
    kind: Literal['project'] = 'project'
    spec: Spec
    metadata: MetadataSpec
