"""
Tests noops.hpr
"""

import os
from io import BytesIO
from unittest.mock import patch, call
from pathlib import Path
from noops.hpr import wrapper
from .test_noops import product_copy
from . import TestCaseNoOps

DATA=Path("tests/data/hpr").resolve()

class Test(TestCaseNoOps):
    """
    Tests noops.hpr
    """
    class StdinBuffer(): # pylint: disable=too-few-public-methods
        """Stdin.buffer mock"""
        def __init__(self, buffer):
            self.buffer = buffer

    @patch("noops.hpr.execute")
    def test_wrapper(self, mock_execute):
        """Kustomize"""

        with product_copy(DATA) as product_path:
            charts = (product_path / "charts.yaml").read_text(encoding="UTF-8")

            os.chdir(os.fspath(product_path))

            with patch('sys.stdin', Test.StdinBuffer(BytesIO(charts.encode()))) as stdin:
                wrapper()

                self.assertEqual(stdin.buffer.read(), b"") # all has been read
                self.assertEqual(
                    mock_execute.call_args_list[0],
                    call('kustomize', ['build', 'kustomize/test'])
                )

            # copy output to all.yaml
            self.assertEqual(
                (product_path / "kustomize/base/all.yaml").read_text(encoding="UTF-8"),
                (product_path / "charts.yaml").read_text(encoding="UTF-8")
            )
