"""
Tests relative to Targets Kind actions (mostly targets.py)
"""

from pathlib import Path
from noops.targets import Targets
from noops.typing.targets import (
    TargetPlan, TargetClassesEnum, TargetsEnum, TargetKind,
    MatchExpressionsSpec,
    TargetClasses, Cluster
)
from noops.errors import TargetNotSupported, TargetPlanUnknown, ClustersAvailability
from noops.utils.io import read_yaml

from . import TestCaseNoOps

class TestTargets(TestCaseNoOps):
    """
    Tests relative to Targets Kind actions
    """
    def test_verify_one_cluster(self):
        """
        Verify [one cluster]
        """
        plan = TargetPlan()
        plan.target_class = TargetClassesEnum.ONE_CLUSTER
        targets = Targets({})

        supported: TargetClasses = TargetClasses.model_validate(
            {
                "one-cluster":True,
                "multi-cluster":True,
                "active-standby":True
            }
        )

        self.assertRaises(
            TargetNotSupported, targets.verify, plan, TargetsEnum.MULTI_CLUSTER, supported)
        self.assertRaises(TargetNotSupported, targets.verify, plan, TargetsEnum.ACTIVE, supported)
        self.assertRaises(TargetNotSupported, targets.verify, plan, TargetsEnum.STANDBY, supported)

    def test_verify_multi_cluster(self):
        """
        Verify [multi-cluster]
        """
        plan = TargetPlan()
        plan.target_class = TargetClassesEnum.MULTI_CLUSTER
        targets = Targets({})

        supported: TargetClasses = TargetClasses.model_validate(
            {
                "one-cluster":True,
                "multi-cluster":True,
                "active-standby":True
            }
        )

        self.assertRaises(
            TargetNotSupported, targets.verify, plan, TargetsEnum.ONE_CLUSTER, supported)
        self.assertRaises(TargetNotSupported, targets.verify, plan, TargetsEnum.ACTIVE, supported)
        self.assertRaises(TargetNotSupported, targets.verify, plan, TargetsEnum.STANDBY, supported)

    def test_verify_active_standby(self):
        """
        Verify [active-standby]
        """
        plan = TargetPlan()
        plan.target_class = TargetClassesEnum.ACTIVE_STANDBY
        targets = Targets({})

        supported: TargetClasses = TargetClasses.model_validate(
            {
                "one-cluster":True,
                "multi-cluster":True,
                "active-standby":True
            }
        )

        self.assertRaises(
            TargetNotSupported, targets.verify, plan, TargetsEnum.ONE_CLUSTER, supported)
        self.assertRaises(
            TargetNotSupported, targets.verify, plan, TargetsEnum.MULTI_CLUSTER, supported)

    def test_verify_invalid_target(self):
        """
        Verify Invalid Target
        """
        plan = TargetPlan()
        targets = Targets({})
        supported: TargetClasses = TargetClasses()

        self.assertRaises(
            TargetNotSupported, targets.verify, plan, "SOMETHINGELSE", supported)

    def test_helm_args(self):
        """Helm Arguments for a target"""

        supported: TargetClasses = TargetClasses.model_validate(
            {
                "one-cluster":True,
                "multi-cluster":True,
                "active-standby":True
            }
        )
        env = "test"
        path = Path("tests/data/targets")

        # target is unset
        self.assertEqual(Targets.helm_targets_args(supported, None, env, path), [])

        # target not compatible
        self.assertRaises(
            TargetNotSupported, Targets.helm_targets_args, supported, "SOMETHINGELSE", env, path)

        # args
        self.assertEqual(
            Targets.helm_targets_args(supported, TargetsEnum.ONE_CLUSTER, env, path),
            [
                '-f',
                'tests/data/targets/noops/target-one-cluster-default.yaml',
                '-f',
                'tests/data/targets/noops/target-one-cluster-test.yaml',
                '-f',
                'tests/data/targets/noops/target-one-cluster.yaml'
            ]
        )

        self.assertEqual(
            Targets.helm_targets_args(supported, TargetsEnum.ONE_CLUSTER, "fake_env", path),
            [
                '-f',
                'tests/data/targets/noops/target-one-cluster-default.yaml',
                '-f',
                'tests/data/targets/noops/target-one-cluster.yaml'
            ]
        )

    def test_init(self):
        """
        Initialize clusters settings
        """
        clusters = read_yaml("tests/data/targets/clusters.yaml")
        targets = Targets(clusters)
        self.assertIsInstance(targets.get_clusters(), list)
        self.assertIsInstance(targets.get_clusters_name(), list)
        self.assertEqual(len(clusters), len(targets.get_clusters()))
        self.assertEqual(len(clusters), len(targets.get_clusters_name()))

        targets = Targets([ Cluster.model_validate(i) for i in clusters ])
        self.assertEqual(len(clusters), len(targets.get_clusters()))

    def test_plan(self):
        """
        Plan creation
        """
        clusters = read_yaml("tests/data/targets/clusters.yaml")
        targets = Targets(clusters)
        k: TargetKind = TargetKind.model_validate(read_yaml("tests/data/targets/targets.yaml"))

        # No active
        self.assertRaises(TargetPlanUnknown, targets.plan, k)

        # One cluster
        k.spec.active.clusterCount = 1
        plan = targets.plan(k)
        self.assertEqual(plan.target_class, TargetClassesEnum.ONE_CLUSTER)
        self.assertListEqual(plan.active, ["c1"])
        self.assertListEqual(plan.standby, [])

        # Multi Cluster
        k.spec.active.clusterCount = 2
        plan = targets.plan(k)
        self.assertEqual(plan.target_class, TargetClassesEnum.MULTI_CLUSTER)
        self.assertListEqual(plan.active, ["c1", "c2"])
        self.assertListEqual(plan.standby, [])
        self.assertListEqual(plan.services_only, [])

        # Active-Standby
        k.spec.standby.clusterCount = 1
        plan = targets.plan(k)
        self.assertEqual(plan.target_class, TargetClassesEnum.ACTIVE_STANDBY)
        self.assertListEqual(plan.active, ["c1", "c2"])
        self.assertListEqual(plan.standby, ["c4"])
        self.assertListEqual(plan.services_only, [])

        # Service Only
        k.spec.services_only.clusterCount = "Remaining"
        plan = targets.plan(k)
        self.assertEqual(plan.target_class, TargetClassesEnum.ACTIVE_STANDBY)
        self.assertListEqual(plan.active, ["c1", "c2"])
        self.assertListEqual(plan.standby, ["c4"])
        self.assertListEqual(plan.services_only, ["c3"])

        # active clusterCount negative !
        k.spec.active.clusterCount = -1
        self.assertRaises(TargetPlanUnknown, targets.plan, k)

        # Not enough clusters
        k.spec.active.clusterCount = 10
        self.assertRaises(ClustersAvailability, targets.plan, k)

        # Invalid clusterCount
        k.spec.active.clusterCount = "TEST"
        self.assertRaises(ValueError, targets.plan, k)

    def test_cluster_match(self):
        """
        Cluster match expressions
        """
        cluster: Cluster = Cluster.model_validate({
            "name": "c1",
            "labels": {
                "service/status": "active"
            }
        })

        data = read_yaml("tests/data/targets/match_expressions.yaml")
        me0: MatchExpressionsSpec = MatchExpressionsSpec.model_validate(data[0])
        me1: MatchExpressionsSpec = MatchExpressionsSpec.model_validate(data[1])
        me2: MatchExpressionsSpec = MatchExpressionsSpec.model_validate(data[2])
        me3: MatchExpressionsSpec = MatchExpressionsSpec.model_validate(data[3])

        # In
        self.assertTrue(cluster.match(me0.matchExpressions))

        # NotIn
        self.assertFalse(cluster.match(me1.matchExpressions))

        # Exists
        self.assertTrue(cluster.match(me2.matchExpressions))

        # DoesNotExist
        self.assertFalse(cluster.match(me3.matchExpressions))
