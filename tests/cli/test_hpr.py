"""
Tests cli.hpr
"""

from unittest.mock import patch
from click.testing import CliRunner
from noops.cli.hpr import cli
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests cli.hpr
    """
    @patch("noops.cli.hpr.wrapper")
    def test_hpr(self, mock_wrapper):
        """hpr"""

        runner = CliRunner()

        result = runner.invoke(
            cli
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_wrapper.call_count, 1)
