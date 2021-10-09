"""
NoOps Profiles
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

import os
import errno
from typing import List, Optional
from pathlib import Path
from .typing.profiles import ProfileClasses, ProfileEnum
from .errors import ProfileNotSupported

class Profiles():
    """
    Profiles permits to:
    - check NoOps Helm Package compatibility
    - create helm arguments
    """
    @classmethod
    def is_compatible(cls, profile: ProfileEnum, supported: ProfileClasses) -> bool:
        """
        Verify if NoOps Project (by noops.yaml) support the profile
        """
        if profile in (ProfileEnum.CANARY, ProfileEnum.CANARY_ENDPOINTS_ONLY):
            return supported.canary

        if profile == ProfileEnum.DEDICATED_ENDPOINTS:
            return supported.dedicated_endpoints

        if profile == ProfileEnum.SERVICES_ONLY:
            return supported.services_only

        return False

    @classmethod
    def helm_profiles_args(cls, supported: ProfileClasses, profiles: Optional[List[ProfileEnum]],
        dst: Path) -> List[str]:
        """
        Create profiles arguments to use
        """
        profiles_args=[]

        if profiles is None:
            return profiles_args

        # Check profile settings
        if len(profiles) == 2:
            if ProfileEnum.CANARY in profiles and ProfileEnum.DEDICATED_ENDPOINTS not in profiles:
                raise ProfileNotSupported(canary_conflict=True)
        elif len(profiles) > 1:
            raise ProfileNotSupported(multi_conflict=True)

        for profile in profiles:
            # check compatibility
            if not cls.is_compatible(profile, supported):
                raise ProfileNotSupported(profile=profile)

            values_file = dst / "noops" / f"profile-{profile}.yaml"
            if not values_file.exists():
                raise FileNotFoundError(
                    errno.ENOENT,
                    os.strerror(errno.ENOENT),
                    values_file
                )

            profiles_args.append("-f")
            profiles_args.append(os.fspath(values_file))

        return profiles_args
