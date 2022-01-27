"""
Tests noops.profiles
"""

from pathlib import Path
from noops.profiles import Profiles
from noops.typing.profiles import ProfileClasses, ProfileEnum
from noops.errors import ProfileNotSupported
from . import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.profiles
    """
    def test_profile_default_compatibilities(self):
        """Profiles support against default compatibilities"""
        supported = ProfileClasses()

        self.assertTrue(
            Profiles.is_compatible(ProfileEnum.DEFAULT, supported)
        )
        self.assertFalse(
            Profiles.is_compatible(ProfileEnum.CANARY, supported)
        )
        self.assertFalse(
            Profiles.is_compatible(ProfileEnum.CANARY_ENDPOINTS_ONLY, supported)
        )
        self.assertFalse(
            Profiles.is_compatible(ProfileEnum.CANARY_DEDICATED_ENDPOINTS, supported)
        )
        self.assertFalse(
            Profiles.is_compatible(ProfileEnum.SERVICES_ONLY, supported)
        )
        self.assertFalse(
            Profiles.is_compatible("ANYTHINGELSE" , supported)
        )

    def test_profile_all_compatibilities(self):
        """Profiles support against full compatibilities"""
        supported = ProfileClasses.parse_obj({
            "canary": True,
            "services-only": True
        })

        self.assertTrue(
            Profiles.is_compatible(ProfileEnum.DEFAULT, supported)
        )
        self.assertTrue(
            Profiles.is_compatible(ProfileEnum.CANARY, supported)
        )
        self.assertTrue(
            Profiles.is_compatible(ProfileEnum.CANARY_ENDPOINTS_ONLY, supported)
        )
        self.assertTrue(
            Profiles.is_compatible(ProfileEnum.CANARY_DEDICATED_ENDPOINTS, supported)
        )
        self.assertTrue(
            Profiles.is_compatible(ProfileEnum.SERVICES_ONLY, supported)
        )
        self.assertFalse(
            Profiles.is_compatible("ANYTHINGELSE" , supported)
        )

    def test_helm_profiles_list(self):
        """Profiles list combinaison"""
        supported = ProfileClasses.parse_obj({
            "canary": True,
            "services-only": True
        })

        self.assertRaises(
            ProfileNotSupported,
            lambda: Profiles.helm_profiles_args(
                supported, [], None)
        )

        self.assertRaises(
            ProfileNotSupported,
            lambda: Profiles.helm_profiles_args(
                supported, [ProfileEnum.DEFAULT,None,None], None)
        )

        self.assertRaises(
            ProfileNotSupported,
            lambda: Profiles.helm_profiles_args(
                supported, [ProfileEnum.DEFAULT,None,None,None], None)
        )

    def test_missing_values(self):
        """Missing profile values"""

        self.assertRaises(
            FileNotFoundError,
            lambda: Profiles.helm_profiles_args(
                ProfileClasses(), [ProfileEnum.DEFAULT], Path("does/not/exist/"))
        )

    def test_not_compatible(self):
        """Profile not compatible during helm args"""

        self.assertRaises(
            ProfileNotSupported,
            lambda: Profiles.helm_profiles_args(
                ProfileClasses(),
                [ProfileEnum.DEFAULT, "ANYTHINGELSE"],
                Path("tests/data/profiles")
            )
        )

    def test_profiles_arguments(self):
        """Helm arguments based on profiles"""
        self.assertEqual(
            Profiles.helm_profiles_args(
                ProfileClasses(canary=True),
                [ProfileEnum.DEFAULT, ProfileEnum.CANARY],
                Path("tests/data/profiles")
            ),
            [
                "-f", "tests/data/profiles/noops/profile-default.yaml",
                "-f", "tests/data/profiles/noops/profile-canary.yaml"
            ]
        )
