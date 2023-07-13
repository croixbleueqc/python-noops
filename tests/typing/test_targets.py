"""
Tests noops.typing.projects
"""

from noops.typing import targets
from .. import TestCaseNoOps

class Test(TestCaseNoOps):
    """
    Tests noops.typing.targets
    """
    def test_default_target_kind(self):
        """Default Target Kind"""

        ktarget = targets.TargetKind(
            spec={
                "active": {},
                "standby": {}
            }
        )

        self.assertEqual(
            ktarget.dict(by_alias=True),
            {
                "apiVersion": "noops.local/v1alpha1",
                "kind": "Target",
                "spec": {
                    "active": {
                        "clusterAffinity": None,
                        "clusterCount": 0
                    },
                    "standby": {
                        "clusterAffinity": None,
                        "clusterCount": 0
                    },
                    "services-only": None
                }
            }
        )

    def test_cluster_affinity(self):
        """Cluster Affinity"""

        affinity = targets.ClusterAffinitySpec(
            requiredDuringSchedulingIgnoredDuringExecution={
                "clusterSelectorTerms": []
            }
        )

        self.assertEqual(
            affinity.dict(),
            {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "clusterSelectorTerms": []
                }
            }
        )

    def test_match_expression(self):
        """Match Expression"""

        match = targets.MatchExpressionSpec(
            key="name",
            operator="Exists",
        )

        self.assertEqual(
            match.dict(),
            {
                "key": "name",
                "operator": "Exists",
                "values": None
            }
        )

    def test_operator(self):
        """Operator Entries"""

        self.assertEqual(
            targets.OperatorSpec.list(),
            [
                "In",
                "NotIn",
                "Exists",
                "DoesNotExist"
            ]
        )

    def test_targetclasses(self):
        """TargetClasses Entries"""

        self.assertEqual(
            targets.TargetClassesEnum.list(),
            [
                "one-cluster",
                "multi-cluster",
                "active-standby"
            ]
        )

    def test_targets(self):
        """Targets Entries"""

        self.assertEqual(
            targets.TargetsEnum.list(),
            [
                "one-cluster",
                "multi-cluster",
                "active",
                "standby"
            ]
        )

    def test_default_targetplan(self):
        """Default TargetPlan"""

        ktplan = targets.TargetPlan()

        self.assertEqual(
            ktplan.dict(by_alias=True),
            {
                "target-class": "one-cluster",
                "active": [],
                "standby": [],
                "services-only": []
            }
        )

    def test_default_targetclasses(self):
        """Default TargetClasses"""

        targetclasses = targets.TargetClasses()

        self.assertEqual(
            targetclasses.dict(by_alias=True),
            {
                "one-cluster": False,
                "multi-cluster": False,
                "active-standby": False
            }
        )

    def test_default_cluster(self):
        """Default Cluster"""
        cluster = targets.Cluster(
            name="c1",
            labels={
                "gpgpu": "amd"
            }
        )

        self.assertEqual(
            cluster.model_dump(),
            {
                "name": "c1",
                "labels": {
                    "gpgpu": "amd"
                }
            }
        )
