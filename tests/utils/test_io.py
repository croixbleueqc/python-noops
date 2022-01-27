"""
Tests noops.utils.io
"""

from unittest.mock import patch
import tempfile
from pathlib import Path
from noops.utils.io import write_yaml, read_yaml, write_json, write_raw
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.utils.io
    """
    @patch('builtins.print')
    def test_read_write_yaml(self, mock_print):
        """
        Read and write yaml file
        """
        content = {
            "metadata": {
                "version": 1,
                "path": Path("/a/path")
            }
        }

        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = Path(tmp) / "test.yaml"

            # Write
            write_yaml(file_path, content)
            self.assertTrue(file_path.exists())

            # Read
            read_content = read_yaml(file_path)
            self.assertEqual(read_content, content)

            # Write / Dry run
            file_path.unlink()
            write_yaml(file_path, content, dry_run=True)
            mock_print.assert_called_with("metadata:\n  path: !path '/a/path'\n  version: 1\n")
            self.assertFalse(file_path.exists())

    @patch('builtins.print')
    def test_write_json(self, mock_print):
        """
        Write json file
        """
        content = {
            "metadata": {
                "version": 1,
                "path": Path("/a/path")
            }
        }

        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = Path(tmp) / "test.json"

            # Write
            write_json(file_path, content)
            self.assertTrue(file_path.exists())

            # Write / Dry run
            file_path.unlink()
            write_json(file_path, content, dry_run=True)
            mock_print.assert_called_with(
                '{\n  "metadata": {\n    "version": 1,\n    "path": "/a/path"\n  }\n}'
            )
            self.assertFalse(file_path.exists())

    @patch('builtins.print')
    def test_write_raw(self, mock_print):
        """
        Write raw file
        """
        content = "test"

        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = Path(tmp) / "test.raw"

            # Write
            write_raw(file_path, content)
            self.assertTrue(file_path.exists())

            # Write / Dry run
            file_path.unlink()
            write_raw(file_path, content, dry_run=True)
            mock_print.assert_called_with('test')
            self.assertFalse(file_path.exists())
