"""
Tests relative to Targets Kind actions (mostly targets.py)
"""

from noops.targets import Targets
from noops.typing.targets import (
    Plan, TargetClassesEnum, TargetsEnum, Kind,
    MatchExpressionsSpec,
    TargetClasses, Cluster
)
from noops.errors import TargetNotSupported, PlanTargetUnknown, ClustersAvailability
from noops.utils.io import read_yaml

from . import TestCaseNoOps

class TestTargets(TestCaseNoOps):
    """
    Tests relative to Targets Kind actions
    """
    def test_verify_one_cluster(self):
        """
        Helm flags [one cluster]
        """
        plan = Plan()
        plan.target = TargetClassesEnum.ONE_CLUSTER
        targets = Targets({})

        supported: TargetClasses = TargetClasses.parse_obj(
            {
                "one-cluster":True,
                "multi-cluster":False,
                "active-standby":False
            }
        )

        self.assertRaises(
            TargetNotSupported, targets.verify, plan, TargetsEnum.MULTI_CLUSTER, supported)
        self.assertRaises(TargetNotSupported, targets.verify, plan, TargetsEnum.ACTIVE, supported)
        self.assertRaises(TargetNotSupported, targets.verify, plan, TargetsEnum.STANDBY, supported)

    def test_verify_multi_cluster(self):
        """
        Helm flags [multi-cluster]
        """
        plan = Plan()
        plan.target = TargetClassesEnum.MULTI_CLUSTER
        targets = Targets({})

        supported: TargetClasses = TargetClasses.parse_obj(
            {
                "one-cluster":False,
                "multi-cluster":True,
                "active-standby":False
            }
        )

        self.assertRaises(
            TargetNotSupported, targets.verify, plan, TargetsEnum.ONE_CLUSTER, supported)
        self.assertRaises(TargetNotSupported, targets.verify, plan, TargetsEnum.ACTIVE, supported)
        self.assertRaises(TargetNotSupported, targets.verify, plan, TargetsEnum.STANDBY, supported)

    def test_verify_active_standby(self):
        """
        Helm flags [active-standby]
        """
        plan = Plan()
        plan.target = TargetClassesEnum.ACTIVE_STANDBY
        targets = Targets({})

        supported: TargetClasses = TargetClasses.parse_obj(
            {
                "one-cluster":False,
                "multi-cluster":False,
                "active-standby":True
            }
        )

        self.assertRaises(
            TargetNotSupported, targets.verify, plan, TargetsEnum.ONE_CLUSTER, supported)
        self.assertRaises(
            TargetNotSupported, targets.verify, plan, TargetsEnum.MULTI_CLUSTER, supported)

    def test_init(self):
        """
        Initialize clusters settings
        """
        clusters = read_yaml("tests/data/clusters.yaml")
        targets = Targets(clusters)
        self.assertIsInstance(targets.get_clusters(), list)
        self.assertIsInstance(targets.get_clusters_name(), list)
        self.assertEqual(len(clusters), len(targets.get_clusters()))
        self.assertEqual(len(clusters), len(targets.get_clusters_name()))

    def test_compute(self):
        """
        Plan creation
        """
        clusters = read_yaml("tests/data/clusters.yaml")
        targets = Targets(clusters)
        k: Kind = Kind.parse_obj(read_yaml("tests/data/targets.yaml"))

        # No active
        self.assertRaises(PlanTargetUnknown, targets.compute, k)

        # One cluster
        k.spec.active.clusterCount = 1
        plan = targets.compute(k)
        self.assertEqual(plan.target, TargetClassesEnum.ONE_CLUSTER)
        self.assertListEqual(plan.active, ["c1"])
        self.assertListEqual(plan.standby, [])

        # Multi Cluster
        k.spec.active.clusterCount = 2
        plan = targets.compute(k)
        self.assertEqual(plan.target, TargetClassesEnum.MULTI_CLUSTER)
        self.assertListEqual(plan.active, ["c1", "c2"])
        self.assertListEqual(plan.standby, [])
        self.assertListEqual(plan.service_only, [])

        # Active-Standby
        k.spec.standby.clusterCount = 1
        plan = targets.compute(k)
        self.assertEqual(plan.target, TargetClassesEnum.ACTIVE_STANDBY)
        self.assertListEqual(plan.active, ["c1", "c2"])
        self.assertListEqual(plan.standby, ["c4"])
        self.assertListEqual(plan.service_only, [])

        # Service Only
        k.spec.service_only.clusterCount = "Remaining"
        plan = targets.compute(k)
        self.assertEqual(plan.target, TargetClassesEnum.ACTIVE_STANDBY)
        self.assertListEqual(plan.active, ["c1", "c2"])
        self.assertListEqual(plan.standby, ["c4"])
        self.assertListEqual(plan.service_only, ["c3"])

        # active clusterCount negative !
        k.spec.active.clusterCount = -1
        self.assertRaises(PlanTargetUnknown, targets.compute, k)

        # Not enough clusters
        k.spec.active.clusterCount = 10
        self.assertRaises(ClustersAvailability, targets.compute, k)

        # Invalid clusterCount
        k.spec.active.clusterCount = "TEST"
        self.assertRaises(ValueError, targets.compute, k)

    def test_cluster_match(self):
        """
        Cluster match expressions
        """
        cluster: Cluster = Cluster.parse_obj({
            "name": "c1",
            "labels": {
                "service/status": "active"
            }
        })

        data = read_yaml("tests/data/match_expressions.yaml")
        me0: MatchExpressionsSpec = MatchExpressionsSpec.parse_obj(data[0])
        me1: MatchExpressionsSpec = MatchExpressionsSpec.parse_obj(data[1])
        me2: MatchExpressionsSpec = MatchExpressionsSpec.parse_obj(data[2])
        me3: MatchExpressionsSpec = MatchExpressionsSpec.parse_obj(data[3])

        # In
        self.assertTrue(cluster.match(me0.matchExpressions))

        # NotIn
        self.assertFalse(cluster.match(me1.matchExpressions))

        # Exists
        self.assertTrue(cluster.match(me2.matchExpressions))

        # DoesNotExist
        self.assertFalse(cluster.match(me3.matchExpressions))
