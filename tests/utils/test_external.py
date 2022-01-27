"""
Tests noops.utils.external
"""

import tempfile
from pathlib import Path
from noops.utils.external import execute, get_stdout
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.utils.external
    """
    def test_execute(self):
        """
        Execute
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
        Execute from a shell
        """
        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = Path(tmp) / "test.execute_from_shell"

            execute(f"touch {file_path}", shell=True)

            self.assertTrue(file_path.exists())

    def test_stdout_from_shell(self):
        """
        Get external command output from a shell
        """
        output = get_stdout(
            execute("echo 'TEST'", shell=True, capture_output=True)
        )
        self.assertEqual(output, "TEST")
