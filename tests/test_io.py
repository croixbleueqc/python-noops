"""
Tests relative to io
"""

from unittest.mock import patch
import tempfile
import os
from noops.utils.io import write_yaml, read_yaml, write_json, write_raw
from . import TestCaseNoOps

class TestIO(TestCaseNoOps):
    """
    Tests relative to io
    """
    @patch('builtins.print')
    def test_read_write_yaml(self, mock_print):
        """
        Read and write yaml file
        """
        content = {
            "metadata": {
                "version": 1
            }
        }

        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = os.path.join(tmp, "test.yaml")

            # Write
            write_yaml(file_path, content)
            self.assertTrue(os.path.exists(file_path))

            # Read
            read_content = read_yaml(file_path)
            self.assertEqual(read_content, content)

            # Write / Dry run
            os.remove(file_path)
            write_yaml(file_path, content, dry_run=True)
            mock_print.assert_called_with('metadata:\n  version: 1\n')
            self.assertFalse(os.path.exists(file_path))

    @patch('builtins.print')
    def test_write_json(self, mock_print):
        """
        Write json file
        """
        content = {
            "metadata": {
                "version": 1
            }
        }

        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = os.path.join(tmp, "test.json")

            # Write
            write_json(file_path, content)
            self.assertTrue(os.path.exists(file_path))

            # Write / Dry run
            os.remove(file_path)
            write_json(file_path, content, dry_run=True)
            mock_print.assert_called_with('{\n  "metadata": {\n    "version": 1\n  }\n}')
            self.assertFalse(os.path.exists(file_path))

    @patch('builtins.print')
    def test_write_raw(self, mock_print):
        """
        Write raw file
        """
        content = "test"

        with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
            file_path = os.path.join(tmp, "test.raw")

            # Write
            write_raw(file_path, content)
            self.assertTrue(os.path.exists(file_path))

            # Write / Dry run
            os.remove(file_path)
            write_raw(file_path, content, dry_run=True)
            mock_print.assert_called_with('test')
            self.assertFalse(os.path.exists(file_path))
