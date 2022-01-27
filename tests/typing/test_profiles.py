"""
Tests noops.typing.profiles
"""

from noops.typing import profiles
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.typing.profiles
    """
    def test_profile_classes(self):
        """
        Profile Classes
        """

        profileclasses = profiles.ProfileClasses()

        self.assertEqual(profileclasses.dict(by_alias=True), {
            "canary": False,
            "services-only": False
        })

    def test_profile_enum(self):
        """
        Profile Enum entries
        """
        self.assertEqual(
            profiles.ProfileEnum.list(),
            [
                "default",
                "canary",
                "canary-endpoints-only",
                "canary-dedicated-endpoints",
                "services-only"
            ]
        )
