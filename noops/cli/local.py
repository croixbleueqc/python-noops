"""
noopsctl local build
noopsctl local run
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
import click
from . import cli, create_noops_instance
from ..utils.external import execute

@cli.group()
def local():
    """build and run locally"""

@local.command()
@click.pass_obj
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def build(shared, cargs):
    """build your product locally"""

    core = create_noops_instance(shared)

    execute(
        core.noops_config["local"]["build"][os.name],
        list(cargs),
        core.noops_envs(),
        dry_run=core.is_dry_run()
    )

@local.command()
@click.pass_obj
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def run(shared, cargs):
    """run your product locally"""

    core = create_noops_instance(shared)

    execute(
        core.noops_config["local"]["run"][os.name],
        list(cargs),
        core.noops_envs(),
        dry_run=core.is_dry_run()
    )
