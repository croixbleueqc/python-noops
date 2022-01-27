"""
Tests noops.typing
"""

from noops.typing import StrEnum
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.typing
    """
    def test_strenum(self):
        """
        StrEnum Structure
        """

        class TestEnum(StrEnum): # pylint:disable=missing-class-docstring
            TEST1="1"
            TEST2="2"

        self.assertEqual(TestEnum.list(), ["1", "2"])
