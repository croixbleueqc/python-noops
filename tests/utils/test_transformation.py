"""
Tests noops.utils.transformation
"""

from noops.utils.transformation import label_rfc1035
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.utils.transformation
    """
    def test_rfc1035(self):
        """
        rfc1035 compliance
        """
        self.assertEqual(label_rfc1035("aer_!"), "aer")
        self.assertEqual(label_rfc1035("aer_!a"), "aer--a")
        self.assertEqual(
            len(
                label_rfc1035(
                    "aer_!111111111111111111111111111111111111111111111111111111111111111"
                )
            ),
            63
        )
