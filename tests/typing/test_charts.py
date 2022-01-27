"""
Tests noops.typing.charts
"""

from noops.typing import charts
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.typing.charts
    """
    def test_default_chart_kind(self):
        """Default Chart Kind"""

        kchart = charts.ChartKind(
            spec={
                "package": {
                    "helm": {}
                }
            }
        )

        self.assertEqual(
            kchart.dict(by_alias=True),
            {
                "apiVersion": "noops.local/v1alpha1",
                "kind": "Chart",
                "spec": {
                    "package": {
                        "helm": {
                            "pre-processing": []
                        },
                        "supported": None
                    }
                }
            }
        )

    def test_all_chart_kind(self):
        """All field usage for Chart Kind"""

        kchart = charts.ChartKind(
            spec={
                "package": {
                    "helm": {}
                }
            }
        )
        kchart.spec.package.supported = charts.SupportedSpec.parse_obj({
            "profile-classes":{},
            "target-classes":{}
        })

        self.assertEqual(
            kchart.dict(by_alias=True),
            {
                "apiVersion": "noops.local/v1alpha1",
                "kind": "Chart",
                "spec": {
                    "package": {
                        "helm": {
                            "pre-processing": []
                        },
                        "supported": {
                            "profile-classes": {
                                "canary": False,
                                "services-only": False
                            },
                            "target-classes": {
                                "one-cluster": False,
                                "multi-cluster": False,
                                "active-standby": False
                            }
                        }
                    }
                }
            }
        )
