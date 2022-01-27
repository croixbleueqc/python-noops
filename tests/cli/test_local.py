"""
Tests cli.local
"""

import os
from pathlib import Path
from click.testing import CliRunner
from noops.cli.main import cli
from .. import TestCaseNoOps
from ..test_noops import product_copy

PRODUCT=Path("tests/data/cli/product/demo").resolve()

class Test(TestCaseNoOps):
    """
    Tests cli.local
    """
    def test_cli_local(self):
        """
        noopsctl local
        """
        with product_copy(PRODUCT) as product_path:
            runner = CliRunner()

            # Local build
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "local",
                    "build"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".devops.local.build").exists())

            # Local run
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "local",
                    "run"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".devops.local.run").exists())
