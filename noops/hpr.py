"""
Noops Helm Post Renderer handler

Wrapper between helm and kustomize to use helm --post-renderer
"""

# Copyright 2022 Croix Bleue du Québec

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

import sys
import os
from pathlib import Path
from .utils.io import read_yaml
from .utils.external import execute
from . import settings

def wrapper():
    """
    Read stdin from helm and execute kustomize to provide stdout to helm

    https://helm.sh/docs/topics/advanced/#post-rendering
    """

    # read noopshpr configuration
    # this file is created by NoOps package install step
    hpr = Path(settings.DEFAULT_WORKDIR) / settings.DEFAULT_NOOPS_HPR
    hpr_content = read_yaml(hpr)

    kustomize_base: Path = hpr_content["base"]
    kustomize_build: Path = hpr_content["kustomize"]

    # store helm output to all.yaml (binary copy transiting from memory)
    output = kustomize_base / "all.yaml"
    output.write_bytes(sys.stdin.buffer.read())

    # execute kustomize
    execute(
        "kustomize",
        [
            "build",
            os.fspath(kustomize_build)
        ]
    )
