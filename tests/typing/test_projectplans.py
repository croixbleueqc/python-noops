"""
Tests noops.typing.projectplans
"""

from noops.typing import projectplans
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.typing.projectplans
    """
    def test_default_projectplan_kind(self):
        """Default ProjectPlan Kind"""

        kplan = projectplans.ProjectPlanKind(
            metadata={
                "name": "test",
                "namespace": "ns"
            },
            spec={
                "target-class": "one-cluster"
            }
        )

        self.assertEqual(
            kplan.dict(by_alias=True),
            {
                "apiVersion": "noops.local/v1alpha1",
                "kind": "ProjectPlan",
                "metadata": {
                    "name": "test",
                    "namespace": "ns"
                },
                "spec": {
                    "target-class": "one-cluster",
                    "plan": []
                }
            }
        )

    def test_default_projectplan_spec(self):
        """Default Project Plan Spec"""

        planspec = projectplans.ProjectPlanSpec(
            template={
                "spec": {
                    "package": {
                        "install": {
                            "chart": "a_chart",
                            "env": "test"
                        }
                    }
                }
            }
        )

        self.assertEqual(
            planspec.dict(by_alias=True),
            {
                "clusters": [],
                "template": {
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
            }
        )
