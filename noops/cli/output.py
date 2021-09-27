"""
noopsctl output
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
from ..helper import DEFAULT_INDENT
from . import cli, create_noops_instance

@cli.command()
@click.pass_obj
@click.option('-j', '--json', help='json format', default=False, is_flag=True)
@click.option('-i', '--indent', help='space indentation',
    default=DEFAULT_INDENT, show_default=True, type=click.IntRange(2, 8), metavar='SPACES')
def output(shared, json, indent):
    """display few informations"""
    core = create_noops_instance(shared)
    core.output(asjson=json, indent=indent)
