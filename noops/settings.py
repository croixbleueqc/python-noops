"""
Settings

Defines some default variables
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

VERSION="2.0.0-alpha.1"

DEFAULT_INDENT=2
DEFAULT_NOOPS_FILE="noops.yaml"
DEFAULT_WORKDIR="noops_workdir"
GENERATED_NOOPS="noops-generated"

DEFAULT_FEATURES={
    "service-catalog": True,
    "white-label": False
}

VALUES_SVCAT="svcat"

TMP_PREFIX="noops-"

DEFAULT_PKG_HELM_DEFINITIONS = {
    # Define targets based on target classes supported
    # class one-cluster uses one-cluster
    # class multi-cluster uses multi-cluster
    # class active-standby uses active,standby
    "targets": {
        "one-cluster": {
            "noops": { "target": "one-cluster" }
        },
        "multi-cluster": {
            "noops": { "target": "multi-cluster" }
        },
        "active": {
            "noops": { "target": "active" }
        },
        "standby": {
            "noops": { "target": "standby" }
        }
    },
    # Define profiles based on profile classes supported
    # class canary uses canary, canary-endpoints-only. Optionally dedicated-endpoints
    # class services-only uses services-only
    "profiles": {
        "default": {
            "noops": {
                "canary": { "enabled": False, "instances": [] },
                "endpoints": True,
                "canaryEndpointsOnly": False,
                "servicesOnly": False
            }
        },
        "canary": {
            "noops": { "canary": { "enabled": True }, "endpoints": False }
        },
        "canary-dedicated-endpoints": {
            "noops": { "canary": { "enabled": True }}
        },
        "canary-endpoints-only": {
            "noops": { "canary": { "enabled": True }, "canaryEndpointsOnly" : True }
        },
        "services-only": {
            "noops": { "endpoints": False, "servicesOnly": True }
        }
    }
}

DEFAULT_PKG_HELM_CANARY_KEY="noops.canary"
