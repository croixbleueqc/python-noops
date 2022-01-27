"""
Tests cli.output
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
    Tests cli.output
    """
    def test_cli_output(self):
        """
        noopsctl output
        """

        output_yaml = (PRODUCT / "tests/expected_output.yaml").read_text(encoding='UTF-8')

        with product_copy(PRODUCT) as product_path:
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "output"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                output_yaml.replace('{BASE}', os.fspath(product_path))
            )
