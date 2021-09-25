"""
Tests relative to Targets Kind actions (mostly targets.py)
"""

import unittest

from noops.targets import Targets
from noops.typing.targets import (
    Plan, PlanTarget, Kind,
    MatchExpressionsSpec,
    NoOpsTargetsSupported, Cluster
)
from noops.errors import TargetNotSupported, PlanTargetUnknown, ClustersAvailability
from noops.helper import read_yaml

class TestTargets(unittest.TestCase):
    """
    Tests relative to Targets Kind actions
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_helm_flags_one_cluster(self):
        """
        Helm flags [one cluster]
        """
        plan = Plan()
        plan.target = PlanTarget.ONE_CLUSTER
        targets = Targets({})

        self.assertEqual(
            targets.helm_flags(plan, PlanTarget.ONE_CLUSTER),
            "-f target-one-cluster.yaml"
        )

        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.MULTI_CLUSTER)
        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.ACTIVE_STANDBY)
        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.ACTIVE)
        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.STANDBY)

    def test_helm_flags_multi_cluster(self):
        """
        Helm flags [multi-cluster]
        """
        plan = Plan()
        plan.target = PlanTarget.MULTI_CLUSTER
        targets = Targets({})

        self.assertEqual(
            targets.helm_flags(plan, PlanTarget.MULTI_CLUSTER),
            "-f target-multi-cluster.yaml"
        )

        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.ONE_CLUSTER)
        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.ACTIVE_STANDBY)
        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.ACTIVE)
        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.STANDBY)

    def test_helm_flags_active_standby(self):
        """
        Helm flags [active-standby]
        """
        plan = Plan()
        plan.target = PlanTarget.ACTIVE_STANDBY
        targets = Targets({})

        self.assertEqual(
            targets.helm_flags(plan, PlanTarget.ACTIVE),
            "-f target-active.yaml"
        )
        self.assertEqual(
            targets.helm_flags(plan, PlanTarget.STANDBY),
            "-f target-standby.yaml"
        )

        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.ONE_CLUSTER)
        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.MULTI_CLUSTER)
        self.assertRaises(TargetNotSupported, targets.helm_flags, plan, PlanTarget.ACTIVE_STANDBY)

    def test_is_compatible_one_cluster(self):
        """
        Compatibility [one-cluster]
        """
        plan = Plan()
        plan.target = PlanTarget.ONE_CLUSTER
        targets = Targets({})

        supported: NoOpsTargetsSupported = NoOpsTargetsSupported.parse_obj(
            {
                "one-cluster":True,
                "multi-cluster":False,
                "active-standby":False
            }
        )

        self.assertTrue(targets.is_compatible(plan, supported))
        supported.one_cluster = False
        self.assertFalse(targets.is_compatible(plan, supported))

    def test_is_compatible_multi_cluster(self):
        """
        Compatibility [multi-cluster]
        """
        plan = Plan()
        plan.target = PlanTarget.MULTI_CLUSTER
        targets = Targets({})

        supported: NoOpsTargetsSupported = NoOpsTargetsSupported.parse_obj(
            {
                "one-cluster":False,
                "multi-cluster":True,
                "active-standby":False
            }
        )

        self.assertTrue(targets.is_compatible(plan, supported))
        supported.multi_cluster = False
        self.assertFalse(targets.is_compatible(plan, supported))

    def test_is_compatible_active_standby(self):
        """
        Compatibility [active-standby]
        """
        plan = Plan()
        plan.target = PlanTarget.ACTIVE_STANDBY
        targets = Targets({})

        supported: NoOpsTargetsSupported = NoOpsTargetsSupported.parse_obj(
            {
                "one-cluster":False,
                "multi-cluster":False,
                "active-standby":True
            }
        )

        self.assertTrue(targets.is_compatible(plan, supported))
        supported.active_standby = False
        self.assertFalse(targets.is_compatible(plan, supported))

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
        k.spec.active.clustersCount = 1
        plan = targets.compute(k)
        self.assertEqual(plan.target, PlanTarget.ONE_CLUSTER)
        self.assertListEqual(plan.active, ["c1"])
        self.assertListEqual(plan.standby, [])

        # Multi Cluster
        k.spec.active.clustersCount = 2
        plan = targets.compute(k)
        self.assertEqual(plan.target, PlanTarget.MULTI_CLUSTER)
        self.assertListEqual(plan.active, ["c1", "c2"])
        self.assertListEqual(plan.standby, [])
        self.assertListEqual(plan.service_only, [])

        # Active-Standby
        k.spec.standby.clustersCount = 1
        plan = targets.compute(k)
        self.assertEqual(plan.target, PlanTarget.ACTIVE_STANDBY)
        self.assertListEqual(plan.active, ["c1", "c2"])
        self.assertListEqual(plan.standby, ["c4"])
        self.assertListEqual(plan.service_only, [])

        # Service Only
        k.spec.service_only.clustersCount = "Remaining"
        plan = targets.compute(k)
        self.assertEqual(plan.target, PlanTarget.ACTIVE_STANDBY)
        self.assertListEqual(plan.active, ["c1", "c2"])
        self.assertListEqual(plan.standby, ["c4"])
        self.assertListEqual(plan.service_only, ["c3"])

        # active clustersCount negative !
        k.spec.active.clustersCount = -1
        self.assertRaises(PlanTargetUnknown, targets.compute, k)

        # Not enough clusters
        k.spec.active.clustersCount = 10
        self.assertRaises(ClustersAvailability, targets.compute, k)

        # Invalid clustersCount
        k.spec.active.clustersCount = "TEST"
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
