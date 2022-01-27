"""
Tests cli.version
"""

from pathlib import Path
from click.testing import CliRunner
from noops.cli.main import cli
from noops.settings import VERSION
from .. import TestCaseNoOps
from ..test_noops import product_copy

PRODUCT=Path("tests/data/cli/product/demo").resolve()

class Test(TestCaseNoOps):
    """
    Tests cli.version
    """
    def test_version(self):
        """
        noopsctl version
        """
        with product_copy(PRODUCT) as _:

            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["version"]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.output, f'version: {VERSION}\n')
