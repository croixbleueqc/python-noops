"""
Pipeline Continuous Deployment
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
from typing import List
from ..noops import NoOps
from ..utils.external import execute
from ..package.prepare import prepare

def pipeline_deploy(core: NoOps, scope: str, cargs: List[str]):
    """
    Deploy from a pipeline

    scope: default
    """
    if not core.is_feature_enabled("helm-deployment"):
        _helmless_deployment(core, scope, cargs)
    elif core.is_feature_enabled("white-label"):
        _white_label_deployment(core, scope, cargs)
    else:
        _regular_deployment(core, scope, cargs)


def _white_label_deployment(core: NoOps, scope: str, cargs: List[str]):
    """
    Continuous Deployment with White-Labels
    """
    logging.info("White-label deployment requested")

    extra_envs = core.noops_envs()
    extra_envs["NOOPS_WHITE_LABEL"]="y"

    for branding in core.noops_config["white-label"]:
        extra_envs["NOOPS_WHITE_LABEL_REBRAND"] = branding["rebrand"]
        extra_envs["NOOPS_WHITE_LABEL_MARKETER"] = branding["marketer"]

        logging.info("rebrand %s for %s",
            branding["rebrand"],
            branding["marketer"]
        )

        prepare(core)
        execute(
            core.noops_config["pipeline"]["deploy"][scope],
            cargs,
            extra_envs=extra_envs,
            dry_run=core.is_dry_run()
        )

def _regular_deployment(core: NoOps, scope: str, cargs: List[str]):
    """
    Continuous Deployment (default)
    """
    logging.info("Regular deployment requested")

    prepare(core)
    execute(
        core.noops_config["pipeline"]["deploy"][scope],
        cargs,
        core.noops_envs(),
        dry_run=core.is_dry_run()
    )

def _helmless_deployment(core: NoOps, scope: str, cargs: List[str]):
    """
    Continuous Deployment (helm-less)
    """
    logging.info("Helm-less deployment requested")

    execute(
        core.noops_config["pipeline"]["deploy"][scope],
        cargs,
        core.noops_envs(),
        dry_run=core.is_dry_run()
    )
