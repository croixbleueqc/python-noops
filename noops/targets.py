"""
NoOps Targets

noopsctl targets [-f targets.yaml] compute
"""

# Copyright 2021 Croix Bleue du Québec

# This file is part of python-noops.

# python-noops is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# python-noops is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with python-noops.  If not, see <https://www.gnu.org/licenses/>.

from typing import List
from .typing.targets import (
    Plan, Kind, PlanTarget,
    TargetSpec, RequiredSpec,
    Cluster, NoOpsTargetsSupported)
from .errors import TargetNotSupported, ClustersAvailability, PlanTargetUnknown

class Targets():
    """
    Targets permit to :
    - load clusters configuration (name + labels)
    - compute a plan based on targets kind ans clusters definitions
    - get helm flags to set the target
    """
    def __init__(self, clusters: dict):
        self._clusters = [ Cluster.parse_obj(i) for i in clusters ]
        self._clusters_name = [ i.name for i in self._clusters ]

    def get_clusters(self) -> List[Cluster]:
        """Get the list of clusters"""
        return self._clusters

    def get_clusters_name(self) -> List[str]:
        """Get the list of clusters' name"""
        return self._clusters_name

    def compute(self, kind: Kind) -> Plan:
        """
        Create the plan to apply by selecting clusters to used and target
        """
        plan = Plan()

        clusters_used = [] # updated into _filter_usable_clusters
        plan.active = self._filter_usable_clusters(kind.spec.active, clusters_used)
        plan.standby = self._filter_usable_clusters(kind.spec.standby, clusters_used)
        plan.service_only = self._filter_usable_clusters(kind.spec.service_only, clusters_used)

        if len(plan.standby) == 0:
            if len(plan.active) == 1:
                # target is one-cluster
                plan.target = PlanTarget.ONE_CLUSTER
            elif len(plan.active) > 1:
                # target is multi-cluster
                plan.target = PlanTarget.MULTI_CLUSTER
            else:
                raise PlanTargetUnknown()
        elif len(plan.active) >= 1:
            # target is active-standby
            plan.target = PlanTarget.ACTIVE_STANDBY
        else:
            raise PlanTargetUnknown()

        return plan

    def _filter_usable_clusters(self, target: TargetSpec, clusters_used: List[str]) -> List[str]:
        if isinstance(target.clustersCount, int) and target.clustersCount < 1:
            return []

        if target.clusterAffinity is not None:
            # Match
            clusters_selection = self._find_clusters(
                target.clusterAffinity.requiredDuringSchedulingIgnoredDuringExecution
            )
        else:
            # All
            clusters_selection = self.get_clusters_name().copy()

        # Filter remaining clusters
        for cluster in clusters_used:
            try:
                clusters_selection.remove(cluster)
            except ValueError:
                # cluster used not part of the selection
                pass

        if isinstance(target.clustersCount, int):
            if target.clustersCount > len(clusters_selection):
                raise ClustersAvailability(len(clusters_selection), target.clustersCount)

            clusters_selection = clusters_selection[:target.clustersCount]
            clusters_used.extend(clusters_selection)

            return clusters_selection

        if target.clustersCount == "Remaining":
            clusters_used.extend(clusters_selection)

            return clusters_selection

        raise ValueError(f"clustersCount value {target.clustersCount} is not supported !")

    def _find_clusters(self, required: RequiredSpec) -> List[str]:
        # Use dict to get unique ordered clusters
        clusters_selected = {}

        # OR between term
        for terms in required.clusterSelectorTerms:
            for cluster in self.get_clusters():
                if cluster.match(terms.matchExpressions):
                    clusters_selected[cluster.name] = None

        return list(clusters_selected)

    @classmethod
    def is_compatible(cls, target: PlanTarget, supported: NoOpsTargetsSupported) -> bool:
        """
        Verify if NoOps Project (by noops.yaml) support the target plan
        """
        if target == PlanTarget.ONE_CLUSTER and supported.one_cluster:
            return True

        if target == PlanTarget.MULTI_CLUSTER and supported.multi_cluster:
            return True

        if target in (PlanTarget.ACTIVE_STANDBY, PlanTarget.ACTIVE, PlanTarget.STANDBY) \
            and supported.active_standby:
            return True

        return False

    @classmethod
    def verify(cls, plan: Plan, target: PlanTarget, supported: NoOpsTargetsSupported):
        """Verify compatibility of the plan, target and what is supported"""

        if not cls.is_compatible(target, supported):
            raise TargetNotSupported(target)

        if plan.target == PlanTarget.ONE_CLUSTER and target != PlanTarget.ONE_CLUSTER:
            raise TargetNotSupported(target, PlanTarget.ONE_CLUSTER)

        if plan.target == PlanTarget.MULTI_CLUSTER and target != PlanTarget.MULTI_CLUSTER:
            raise TargetNotSupported(target, PlanTarget.MULTI_CLUSTER)

        if plan.target == PlanTarget.ACTIVE_STANDBY and \
            target != PlanTarget.ACTIVE and \
            target != PlanTarget.STANDBY:
            raise TargetNotSupported(target, PlanTarget.ACTIVE, PlanTarget.STANDBY)
