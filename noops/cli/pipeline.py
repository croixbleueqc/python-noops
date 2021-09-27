"""
noopsctl pipeline image
noopsctl pipeline lib
noopsctl pipeline deploy
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
from . import cli, create_noops_instance

@cli.group()
def pipeline():
    """pipeline control"""

@pipeline.command()
@click.pass_obj
@click.option('--ci', '--continuous-integration',
    help='on commit in a work branch [default]', is_flag=True, default=False)
@click.option('--pr', '--pull-request',
    help='on Pull request', is_flag=True, default=False)
@click.option('--cd', '--continuous-delivery',
    help='on merge in main branch', is_flag=True, default=False)
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def image(shared, ci, pr, cd, cargs): # pylint: disable=invalid-name
    """manages ci, pr or cd steps (image)"""

    if ci + pr + cd > 1:
        raise click.BadParameter(
            "following parameters are mutually exclusive: --ci, --pr, --cd"
        )

    if pr:
        scope = "pr"
    elif cd:
        scope = "cd"
    else:
        scope = "ci"

    core = create_noops_instance(shared)
    core.pipeline_image(scope, list(cargs))

@pipeline.command()
@click.pass_obj
@click.option('--ci', '--continuous-integration',
    help='on commit in a work branch [default]', is_flag=True, default=False)
@click.option('--pr', '--pull-request',
    help='on Pull request', is_flag=True, default=False)
@click.option('--cd', '--continuous-delivery',
    help='on merge in main branch', is_flag=True, default=False)
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def lib(shared, ci, pr, cd, cargs): # pylint: disable=invalid-name
    """manages ci, pr or cd steps (library)"""

    if ci + pr + cd > 1:
        raise click.BadParameter(
            "following parameters are mutually exclusive: --ci, --pr, --cd"
        )

    if pr:
        scope = "pr"
    elif cd:
        scope = "cd"
    else:
        scope = "ci"

    core = create_noops_instance(shared)
    core.pipeline_lib(scope, list(cargs))

@pipeline.command()
@click.pass_obj
@click.option('--default', help='default deployment command [default]', is_flag=True, default=False)
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def deploy(shared, default, cargs): # pylint: disable=unused-argument
    """continuous deployment"""

    scope = "default"

    core = create_noops_instance(shared)
    core.pipeline_deploy(scope, list(cargs))
