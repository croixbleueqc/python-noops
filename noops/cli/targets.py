"""
noopsctl target
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

import click
from ..targets import Targets
from ..typing.targets import Kind
from ..helper import read_yaml, json2yaml
from . import cli

@cli.group()
def targets():
    """targets API"""

@targets.command()
@click.option('-c', '--clusters', help='Clusters configuration', required=True, metavar='YAML')
@click.option('-k', '--kind', help='Target kind configuration', required=True, metavar='YAML')
@click.option('-j', '--json', help='json format', default=False, is_flag=True)
def plan(clusters, kind, json):
    """Generate and show an execution plan"""

    clusters_obj = read_yaml(clusters)
    kind_obj = Kind.parse_obj(read_yaml(kind))

    targets_core = Targets(clusters_obj)
    if json:
        click.echo(
            targets_core.compute(kind_obj).json()
        )
    else:
        click.echo(
            json2yaml(targets_core.compute(kind_obj).json())
        )
