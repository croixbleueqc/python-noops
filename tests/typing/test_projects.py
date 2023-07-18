"""
Tests noops.typing.projects
"""

from noops.typing import projects
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.typing.projects
    """
    def test_default_project_kind(self):
        """Default Project Kind"""

        kproject = projects.ProjectKind(
            metadata={
                "name": "test",
                "namespace": "ns"
            },
            spec={
                "package": {
                    "install": {
                        "chart": "a_chart",
                        "env": "test"
                    }
                }
            }
        )

        self.assertEqual(
            kproject.model_dump(by_alias=True),
            {
                "apiVersion": "noops.local/v1alpha1",
                "kind": "Project",
                "metadata": {
                    "name": "test",
                    "namespace": "ns"
                },
                "spec": {
                    "package": {
                        "install": {
                            "chart": "a_chart",
                            "env": "test",
                            "target": None,
                            "services-only": False,
                            "args": None,
                            "envs": None,
                            "white-label": None
                        }
                    },
                    "versions": {
                        "one": None,
                        "multi": None
                    }
                }
            }
        )

    def test_default_reconciliation(self):
        """Default Project Reconciliation Plan"""

        plan = projects.ProjectReconciliationPlan()

        self.assertEqual(
            plan.model_dump(),
            {
                "added": [],
                "changed": [],
                "removed": [],
                "canary_versions": None,
                "removed_canary": False
            }
        )
