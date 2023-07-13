"""
Versions Typing
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

from typing import List, Optional, Literal
from pydantic import BaseModel, Field # pylint: disable=no-name-in-module
from ..errors import VerifyFailure
from .profiles import ProfileEnum

# Version Kind

class MultiSpec(BaseModel): # pylint: disable=too-few-public-methods
    """Multiple deployments model"""
    app_version: str
    version: Optional[str] = None
    build: Optional[str] = None
    weight: Optional[int] = None
    dedicated_endpoints: Optional[bool] = Field(None, alias='dedicated-endpoints')
    args: Optional[List[str]] = None

    @property
    def profiles(self) -> List[ProfileEnum]:
        """Profiles to use"""
        _profiles = [ProfileEnum.DEFAULT]

        if self.weight is not None:
            # weight set means Canary or Blue/Green deployment
            if self.dedicated_endpoints:
                _profiles.append(ProfileEnum.CANARY_DEDICATED_ENDPOINTS)
            else:
                _profiles.append(ProfileEnum.CANARY)

        return _profiles

class OneSpec(BaseModel): # pylint: disable=too-few-public-methods
    """One deployment model"""
    app_version: str
    version: Optional[str] = None
    build: Optional[str] = None
    args: Optional[List[str]] = None

    @property
    def profiles(self) -> List[ProfileEnum]:
        """Profiles to use"""
        return [ProfileEnum.DEFAULT]

class Spec(BaseModel): # pylint: disable=too-few-public-methods
    """kind spec model"""
    one: Optional[OneSpec] = None
    multi: Optional[List[MultiSpec]] = None

class VersionKind(BaseModel): # pylint: disable=too-few-public-methods
    """Version Kind model"""
    apiVersion: Literal['noops.local/v1alpha1'] = 'noops.local/v1alpha1'
    kind: Literal['Version'] = 'Version'
    spec: Spec

    def verify(self, check=True) -> bool:
        """
        Verify version object settings
        """
        use_one = self.spec.one is not None
        use_multi = self.spec.multi is not None
        use_canary = False
        weight = 0
        app_version_used = []

        if use_one:
            app_version_used.append(self.spec.one.app_version)

        if use_multi:
            for pkg in self.spec.multi:
                if pkg.weight is not None:
                    use_canary = True
                    weight += pkg.weight
                if pkg.app_version in app_version_used:
                    if check:
                        raise VerifyFailure(f"app_version '{pkg.app_version}' is duplicated !")
                    return False

        if use_one and use_canary:
            if check:
                raise VerifyFailure("one and canary can not be used toghether !")
            return False

        if use_canary and weight != 100:
            if check:
                raise VerifyFailure("sum(weight) does not equals 100 !")
            return False

        return True
