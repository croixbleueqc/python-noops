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

from typing import List, Union, Optional, Literal
from pydantic import BaseModel, Field # pylint: disable=no-name-in-module
from . import StrEnum

SERVICES_ONLY="services-only"

class OperatorSpec(StrEnum):
    """Filtering operator enum"""
    IN = 'In'
    NOT_IN = 'NotIn'
    EXISTS = 'Exists'
    DOES_NOT_EXIST = 'DoesNotExist'

class MatchExpressionSpec(BaseModel): # pylint: disable=too-few-public-methods
    """Filtering expression model"""
    key: str
    operator: OperatorSpec
    values: Optional[List[str]]

class MatchExpressionsSpec(BaseModel): # pylint: disable=too-few-public-methods
    """List of filtering expressions model"""
    matchExpressions: List[MatchExpressionSpec]

class RequiredSpec(BaseModel): # pylint: disable=too-few-public-methods
    """requiredDuringSchedulingIgnoredDuringExecution model"""
    clusterSelectorTerms: List[MatchExpressionsSpec]

class ClusterAffinitySpec(BaseModel): # pylint: disable=too-few-public-methods
    """clusterAffinity spec"""
    requiredDuringSchedulingIgnoredDuringExecution: RequiredSpec

class TargetSpec(BaseModel): # pylint: disable=too-few-public-methods
    """active, standby, service-only targets model"""
    clusterAffinity: Optional[ClusterAffinitySpec]
    clusterCount: Union[int, str] = 0

class Spec(BaseModel): # pylint: disable=too-few-public-methods
    """Kind spec model"""
    active: TargetSpec
    standby: TargetSpec
    services_only: TargetSpec = Field(None, alias=SERVICES_ONLY)

class TargetKind(BaseModel): # pylint: disable=too-few-public-methods
    """Kind model"""
    apiVersion: Literal['noops.local/v1alpha1']
    kind: Literal['Target']
    spec: Spec

# Plan compute

class TargetClassesEnum(StrEnum):
    """
    Target classes enumeration
    """
    ONE_CLUSTER = 'one-cluster'
    MULTI_CLUSTER = 'multi-cluster'
    ACTIVE_STANDBY = 'active-standby'

class TargetsEnum(StrEnum):
    """
    Sub class Targets enumeration
    """
    ONE_CLUSTER = 'one-cluster'
    MULTI_CLUSTER = 'multi-cluster'
    ACTIVE = 'active'
    STANDBY = 'standby'

class TargetPlan(BaseModel): # pylint: disable=too-few-public-methods
    """
    Model to provide a plan with clusters to used per target
    """
    target_class: TargetClassesEnum = Field(TargetClassesEnum.ONE_CLUSTER, alias="target-class")
    active: List[str] = []
    standby: List[str] = []
    services_only: List[str] = Field([], alias=SERVICES_ONLY)

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

class TargetClasses(BaseModel): # pylint: disable=too-few-public-methods
    """
    package.supported.target-classes model
    """
    one_cluster: bool = Field(False, alias="one-cluster")
    multi_cluster: bool = Field(False, alias="multi-cluster")
    active_standby: bool = Field(False, alias="active-standby")
