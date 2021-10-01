"""
Tests relative to external
"""

import tempfile
import os
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
            file_path = os.path.join(tmp, "test.execute")

            execute(
                "bash",
                [
                    "-c",
                    f"touch {file_path}"
                ]
            )

            self.assertTrue(os.path.exists(file_path))

            # Execute with Dry run
            os.remove(file_path)
            execute(
                "bash",
                [
                    "-c",
                    f"touch {file_path}"
                ],
                dry_run=True
            )
            self.assertFalse(os.path.exists(file_path))

    def test_execute_from_shell(self):
        """
        Test execute from a shell
        """
        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = os.path.join(tmp, "test.execute_from_shell")

            execute_from_shell(f"touch {file_path}")

            self.assertTrue(os.path.exists(file_path))

    def test_stdout_from_shell(self):
        """
        Test to get output from a command
        """
        output = get_stdout_from_shell("echo 'TEST'")
        self.assertEqual(output, "TEST")
