"""
Profile Typing
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

from pydantic import BaseModel, Field # pylint: disable=no-name-in-module
from . import StrEnum

class ProfileClasses(BaseModel): # pylint: disable=too-few-public-methods
    """
    package.supported.profile-classes model
    """
    canary: bool = False
    blue_green: bool = Field(False, alias='blue-green')
    dedicated_endpoints: bool = Field(False, alias='dedicated-endpoints')
    services_only: bool = Field(False, alias='services-only')

class ProfileEnum(StrEnum):
    """
    Sub class Profile enumeration
    """
    CANARY = 'canary'
    CANARY_ENDPOINTS_ONLY = 'canary-endpoints-only'
    DEDICATED_ENDPOINTS = 'dedicated-endpoints'
    SERVICES_ONLY = 'services-only'
