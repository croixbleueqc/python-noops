"""
Tests noops.typing.metadata
"""

from noops.typing import metadata
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.typing.metadata
    """
    def test_metadata(self):
        """Metadata"""

        meta = metadata.MetadataSpec(
            name="name",
            namespace="ns"
        )

        self.assertEqual(
            meta.model_dump(),
            {
                "name": "name",
                "namespace": "ns"
            }
        )
