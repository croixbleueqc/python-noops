"""
Tests relative to external
"""

import tempfile
from pathlib import Path
from noops.utils.external import execute, execute_from_shell, get_stdout_from_shell
from . import TestCaseNoOps

class TestIO(TestCaseNoOps):
    """
    Tests relative to external
    """
    def test_execute(self):
        """
        Test execute
        """
        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = Path(tmp) / "test.execute"

            execute(
                "bash",
                [
                    "-c",
                    f"touch {file_path}"
                ]
            )

            self.assertTrue(file_path.exists())

            # Execute with Dry run
            file_path.unlink()
            execute(
                "bash",
                [
                    "-c",
                    f"touch {file_path}"
                ],
                dry_run=True
            )
            self.assertFalse(file_path.exists())

    def test_execute_from_shell(self):
        """
        Test execute from a shell
        """
        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = Path(tmp) / "test.execute_from_shell"

            execute_from_shell(f"touch {file_path}")

            self.assertTrue(file_path.exists())

    def test_stdout_from_shell(self):
        """
        Test to get output from a command
        """
        output = get_stdout_from_shell("echo 'TEST'")
        self.assertEqual(output, "TEST")
