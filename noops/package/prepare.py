"""
Prepare for packaging, ci, cd and deploy
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

import logging
from ..noops import NoOps
from ..package.helm import Helm
from ..svcat import ServiceCatalog

def prepare(core: NoOps, helm: Helm = None, chart_name: str = None):
    """
    Generates everything that is needed by the product and set with the noops.yaml

    - Service Catalog
    - Helm values
    """

    if helm is None:
        helm = Helm(core, chart_name)

    # Service Catalog
    if core.is_feature_enabled("service-catalog"):
        ServiceCatalog(core, helm).create_kinds_and_values()
    else:
        logging.info("Service Catalog feature disabled")

    # Helm values-*.yaml
    helm.create_values()
