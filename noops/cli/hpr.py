"""
Noops Helm Post Renderer (hpr)
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

import click
from ..hpr import wrapper

@click.group(
    context_settings=dict(help_option_names=["-h", "--help"]),
    invoke_without_command=True)
def cli():
    """Noops Helm Post Renderer

    HPR is a wrapper between helm and kustomize used in --post-renderer.
    HPR needs to be executed at the product root path
    """
    wrapper()
