"""
Errors modules

All exceptions primitives
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

class NoopsException(Exception):
    """Base Exception for all NoOps Exception"""

class VerifyFailure(NoopsException):
    """Issue with an object validation"""

class ProfileNotSupported(NoopsException):
    """Profile is not supported by this product"""
    def __init__(self, msg=None, profile=None):
        if profile is not None:
            msg = f"{profile} is not supported by this product !"

        NoopsException.__init__(self, msg)

class TargetNotSupported(NoopsException):
    """Target is not supported by this product"""
    def __init__(self, target, expected1=None, expected2=None):
        if expected1 is None:
            msg = f"{target} is not supported by this product !"
        elif expected2 is None:
            msg = f"{target} is not supported for this product. Please strictly use {expected1} !"
        else:
            msg = f"{target} is not supported for this product. " \
                  f"Please strictly use {expected1} or {expected2} !"

        NoopsException.__init__(self, msg)

class TargetPlanUnknown(NoopsException):
    """Parameters do not permit to know the target (eg: active, one-cluste, ...)"""
    def __init__(self):
        NoopsException.__init__(
            self,
            "It is not possible to compute the target. Please verify clustersCount settings !"
        )

class ClustersAvailability(NoopsException):
    """Not Enough clusters available"""
    def __init__(self, available: int, expected: int):
        NoopsException.__init__(self, "{} cluster{} required but only {} available{}".format( # pylint: disable=C0209
            expected,
            "s" if expected > 1 else "",
            available,
            "s" if available > 1 else ""
        ))

class ChartNotFound(NoopsException):
    """Chart not found during a search"""
    def __init__(self, chart: str):
        NoopsException.__init__(self, f"chart not found with keyword {chart} !")

class KustomizeStructure(NoopsException):
    """Bad Kustomize structure"""
    def __init__(self):
        NoopsException.__init__(self, "Kustomize structure is not compliant !")
