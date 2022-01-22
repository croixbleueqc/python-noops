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
import shutil
from pathlib import Path
from ..noops import NoOps
from .helm import Helm
from .svcat import ServiceCatalog

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

    # Embedded kustomize (required for package)
    embedded_kustomize(core)

def embedded_kustomize(core: NoOps):
    """
    Copy kustomize under the helm chart if available and necessary
    """
    kustomize: Path = core.noops_config["package"].get("helm", {}).get("kustomize")

    if kustomize is None:
        # kustomize is not used
        logging.info("kustomize is not used")
        return

    values: Path = core.noops_config["package"]["helm"]["values"]

    if kustomize.parent == values.parent:
        # kustomize is already located under the helm chart (built-in)
        logging.info("Using built-in kustomize")
        return

    # Copy
    logging.info("Embedding kustomize")
    dst = values.parent / "kustomize"
    if dst.exists():
        shutil.rmtree(dst)

    shutil.copytree(
        kustomize,
        dst
    )
