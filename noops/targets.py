"""
NoOps Targets

target.noops.local/v1alpha1
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

import os
from typing import List, Optional
from pathlib import Path
from .typing.targets import (
    Plan, Kind, TargetsEnum, TargetClassesEnum,
    TargetSpec, RequiredSpec,
    Cluster, TargetClasses)
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
                plan.target = TargetClassesEnum.ONE_CLUSTER
            elif len(plan.active) > 1:
                # target is multi-cluster
                plan.target = TargetClassesEnum.MULTI_CLUSTER
            else:
                raise PlanTargetUnknown()
        elif len(plan.active) >= 1:
            # target is active-standby
            plan.target = TargetClassesEnum.ACTIVE_STANDBY
        else:
            raise PlanTargetUnknown()

        return plan

    def _filter_usable_clusters(self, target: TargetSpec, clusters_used: List[str]) -> List[str]:
        if isinstance(target.clusterCount, int) and target.clusterCount < 1:
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

        if isinstance(target.clusterCount, int):
            if target.clusterCount > len(clusters_selection):
                raise ClustersAvailability(len(clusters_selection), target.clusterCount)

            clusters_selection = clusters_selection[:target.clusterCount]
            clusters_used.extend(clusters_selection)

            return clusters_selection

        if target.clusterCount == "Remaining":
            clusters_used.extend(clusters_selection)

            return clusters_selection

        raise ValueError(f"clusterCount value {target.clusterCount} is not supported !")

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
    def is_compatible(cls, target: TargetsEnum, supported: TargetClasses) -> bool:
        """
        Verify if NoOps Project (by noops.yaml) support the target plan
        """
        if target == TargetsEnum.ONE_CLUSTER:
            return supported.one_cluster

        if target == TargetsEnum.MULTI_CLUSTER:
            return supported.multi_cluster

        if target in (TargetsEnum.ACTIVE, TargetsEnum.STANDBY):
            return supported.active_standby

        return False

    @classmethod
    def verify(cls, plan: Plan, target: TargetsEnum, supported: TargetClasses):
        """Verify compatibility of the plan, target and what is supported"""

        if not cls.is_compatible(target, supported):
            raise TargetNotSupported(target)

        if plan.target == TargetClassesEnum.ONE_CLUSTER and target != TargetsEnum.ONE_CLUSTER:
            raise TargetNotSupported(target, TargetsEnum.ONE_CLUSTER)

        if plan.target == TargetClassesEnum.MULTI_CLUSTER and target != TargetsEnum.MULTI_CLUSTER:
            raise TargetNotSupported(target, TargetsEnum.MULTI_CLUSTER)

        if plan.target == TargetClassesEnum.ACTIVE_STANDBY and \
            target != TargetsEnum.ACTIVE and \
            target != TargetsEnum.STANDBY:
            raise TargetNotSupported(target, TargetsEnum.ACTIVE, TargetsEnum.STANDBY)

    @classmethod
    def helm_targets_args(cls, supported: TargetClasses, target: Optional[TargetsEnum],
        env: str, dst: Path) -> List[str]:
        """
        Create targets arguments to use by helm
        """
        targets_args=[]

        if target is None:
            return targets_args

        # check compatibility
        if not cls.is_compatible(target, supported):
            raise TargetNotSupported(target)

        for values in ("-default", f"-{env}", ""):
            values_file = dst / "noops" / f"target-{target.value}{values}.yaml"
            if values_file.exists():
                targets_args.append("-f")
                targets_args.append(os.fspath(values_file))

        return targets_args
