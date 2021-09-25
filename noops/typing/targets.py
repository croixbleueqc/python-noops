"""
Targets Typing
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

from typing import List, Union, Optional
from enum import Enum
from pydantic import BaseModel, Field # pylint: disable=E0611

SERVICE_ONLY="service-only"

class OperatorSpec(str, Enum):
    """Filtering operator enum"""
    IN = 'In'
    NOT_IN = 'NotIn'
    EXISTS = 'Exists'
    DOES_NOT_EXIST = 'DoesNotExist'

class MatchExpressionSpec(BaseModel): # pylint: disable=R0903
    """Filtering expression model"""
    key: str
    operator: OperatorSpec
    values: Optional[List[str]]

class MatchExpressionsSpec(BaseModel): # pylint: disable=R0903
    """List of filtering expressions model"""
    matchExpressions: List[MatchExpressionSpec]

class RequiredSpec(BaseModel): # pylint: disable=R0903
    """requiredDuringSchedulingIgnoredDuringExecution model"""
    clusterSelectorTerms: List[MatchExpressionsSpec]

class ClusterAffinitySpec(BaseModel): # pylint: disable=R0903
    """clusterAffinity spec"""
    requiredDuringSchedulingIgnoredDuringExecution: RequiredSpec

class TargetSpec(BaseModel): # pylint: disable=R0903
    """active, standby, service-only targets model"""
    clusterAffinity: Optional[ClusterAffinitySpec]
    clustersCount: Union[int, str] = 0

class Spec(BaseModel): # pylint: disable=R0903
    """Kind spec model"""
    active: TargetSpec
    standby: TargetSpec
    service_only: TargetSpec = Field(None, alias=SERVICE_ONLY)
    localLoadBalancer: bool = False

class Kind(BaseModel): # pylint: disable=R0903
    """Kind model"""
    apiVersion: str = 'noops.local/v1alpha1'
    kind: str = 'target'
    spec: Spec

# Plan compute

class PlanTarget(str, Enum):
    """Plan and Helm targets enum"""
    ONE_CLUSTER = 'one-cluster'
    MULTI_CLUSTER = 'multi-cluster'
    ACTIVE_STANDBY = 'active-standby'
    ACTIVE = 'active' # Helm only
    STANDBY = 'standby' # Helm only
    UNKNOWN = 'unknown'

class Plan(BaseModel): # pylint: disable=R0903
    """
    Model to provide a plan with clusters to used per target
    """
    target: PlanTarget = PlanTarget.UNKNOWN
    active: List[str] = []
    standby: List[str] = []
    service_only: List[str] = Field([], alias=SERVICE_ONLY)

# Cluster

class Cluster(BaseModel):
    """
    Cluster model

    - name: cluster1
      labels:
        key1: value1
        key2: value2
    """
    name: str
    labels: dict

    def match(self, terms: List[MatchExpressionSpec]) -> bool:
        """Is this cluster compatible with filtering provided ?"""
        # AND between term
        for term in terms:
            matching: bool = False
            if term.operator == OperatorSpec.IN:
                matching = self.is_label_in(term)
            elif term.operator == OperatorSpec.NOT_IN:
                matching = self.is_label_not_in(term)
            elif term.operator == OperatorSpec.EXISTS:
                matching = self.is_label_exists(term)
            else: # term.operator == OperatorSpec.DOES_NOT_EXIST
                matching = self.is_label_does_not_exists(term)

            if not matching:
                # mismatch, no needs to continue
                return False

        # Only if there is no mismatch
        return True

    def is_label_in(self, term: MatchExpressionSpec):
        """Is cluster label value in filtering values ?"""
        return self.labels.get(term.key) in term.values

    def is_label_not_in(self, term: MatchExpressionSpec):
        """Is cluster label value NOT in filtering values ?"""
        return self.labels.get(term.key) not in term.values

    def is_label_exists(self, term: MatchExpressionSpec):
        """Is cluster label exists ?"""
        return term.key in self.labels

    def is_label_does_not_exists(self, term: MatchExpressionSpec):
        """Is cluster label does NOT exist ?"""
        return term.key not in self.labels

# NoOps yaml

class NoOpsTargetsSupported(BaseModel): # pylint: disable=R0903
    """noops.targets.supported model"""
    one_cluster: bool = Field(False, alias="one-cluster")
    multi_cluster: bool = Field(False, alias="multi-cluster")
    active_standby: bool = Field(False, alias="active-standby")
