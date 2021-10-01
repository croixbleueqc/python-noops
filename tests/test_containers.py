"""
Tests relative to containers
"""

from noops.utils.containers import merge
from . import TestCaseNoOps

class TestContainers(TestCaseNoOps):
    """
    Tests relative to containers
    """
    def test_merge(self):
        """
        Merge 2 dict with a deep merge strategy
        """
        product = {
            "metadata": {
                "version": 2
            }
        }

        devops = {
            "metadata": {
                "name": "devops"
            }
        }

        merged = {
            "metadata": {
                "version": 2,
                "name": "devops"
            }
        }

        self.assertEqual(
            merge(devops, product),
            merged
        )
