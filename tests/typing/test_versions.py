"""
Tests noops.typing.versions
"""

from noops.typing import versions
from noops.profiles import ProfileEnum
from noops.errors import VerifyFailure
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.typing.versions
    """

    def test_kind_version(self):
        """Default kind Version"""
        kversion = versions.VersionKind(spec={})

        self.assertEqual(kversion.dict(), {
            "apiVersion": "noops.local/v1alpha1",
            "kind": "Version",
            "spec": {
                "one": None,
                "multi": None
            }
        })

        # verify
        self.assertTrue(kversion.verify())

    def test_one_version(self):
        """With One version"""

        kversion = versions.VersionKind(spec={})
        kversion.spec.one = versions.OneSpec(
            app_version="1.0.0"
        )
        self.assertTrue(kversion.verify())

    def test_multi_one_versions_identical(self):
        """One and Multi version refering the same app version"""

        kversion = versions.VersionKind(spec={})
        kversion.spec.one = versions.OneSpec(
            app_version="1.0.0"
        )
        kversion.spec.multi=[
            versions.MultiSpec(
                app_version="1.0.0"
            )
        ]
        self.assertRaises(VerifyFailure, kversion.verify)
        self.assertFalse(kversion.verify(check=False))

    def test_multi_one_versions_diff(self):
        """One and Multi version refering different app version"""

        kversion = versions.VersionKind(spec={})
        kversion.spec.multi=[
            versions.MultiSpec(
                app_version="2.0.0"
            )
        ]
        self.assertTrue(kversion.verify())

    def test_one_and_canary(self):
        """Multi version as canary and One version together"""

        kversion = versions.VersionKind(spec={})
        kversion.spec.one = versions.OneSpec(
            app_version="1.0.0"
        )
        kversion.spec.multi=[
            versions.MultiSpec(
                app_version="2.0.0",
                weight=10
            )
        ]
        self.assertRaises(VerifyFailure, kversion.verify)
        self.assertFalse(kversion.verify(check=False))

    def test_canary_weight(self):
        """Weight sum"""

        kversion = versions.VersionKind(spec={})
        kversion.spec.multi=[
            versions.MultiSpec(
                app_version="2.0.0",
                weight=10
            )
        ]
        self.assertRaises(VerifyFailure, kversion.verify)
        self.assertFalse(kversion.verify(check=False))

        kversion.spec.multi.append(
            versions.MultiSpec(
                app_version="2.0.0",
                weight=90
            )
        )
        self.assertTrue(kversion.verify())

    def test_one_profile(self):
        """One spec profile and settings"""
        one = versions.OneSpec(
            app_version="1.0.0"
        )

        self.assertEqual(one.dict(), {
            "app_version": "1.0.0",
            "args": None,
            "build": None,
            "version": None
        })

        self.assertEqual(one.profiles, [ProfileEnum.DEFAULT])

    def test_multi_profile(self):
        """Multi spec profile and settings"""
        multi = versions.MultiSpec(
            app_version="1.0.0"
        )

        self.assertEqual(multi.dict(), {
            "app_version": "1.0.0",
            "version": None,
            "build": None,
            "weight": None,
            "dedicated_endpoints": None,
            "args": None
        })

        self.assertEqual(multi.profiles, [ProfileEnum.DEFAULT])

        multi.weight = 10
        self.assertEqual(multi.profiles, [ProfileEnum.DEFAULT, ProfileEnum.CANARY])

        multi.dedicated_endpoints = True
        self.assertEqual(
            multi.profiles,
            [ProfileEnum.DEFAULT, ProfileEnum.CANARY_DEDICATED_ENDPOINTS]
        )
