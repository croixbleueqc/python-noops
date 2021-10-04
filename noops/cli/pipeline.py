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
from ..utils.external import execute
from ..pipeline.deploy import pipeline_deploy

@cli.group()
def pipeline():
    """pipeline control"""

def __image_lib(shared, argument, ci, pr, cd, cargs): # pylint: disable=invalid-name
    """
    Shared logic for continuous integration, pull request and continuous delivery
    ONLY for deprecated image and lib arguments
    """
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

    execute(
        core.noops_config["pipeline"][argument][scope],
        list(cargs),
        core.noops_envs(),
        dry_run=core.is_dry_run()
    )

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
    """manages ci, pr or cd steps (image) [DEPRECATED]"""

    __image_lib(
        shared,
        "image",
        ci, pr, cd,
        cargs
    )

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
    """manages ci, pr or cd steps (library) [DEPRECATED]"""

    __image_lib(
        shared,
        "lib",
        ci, pr, cd,
        cargs
    )

def __ci_pr_cd(shared, target):
    """
    Shared logic for continuous integration, pull request and continuous delivery
    """
    core = create_noops_instance(shared)

    targets = list(core.noops_config["pipeline"].keys())
    try:
        targets.remove("deploy") # reserved key under pipeline for continuous deployment
    except ValueError:
        pass

    if target not in targets:
        raise click.BadArgumentUsage(
            "target '{}' is invalid (accepted: {})".format( # pylint: disable=consider-using-f-string
                target,
                "|".join(targets)
            )
        )

    return core

@pipeline.command(name='ci')
@click.pass_obj
@click.argument('target', nargs=1, required=True)
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def continuous_integration(shared, target, cargs):
    """continuous integration

    TARGET refers to pipeline.<TARGET> (noops.yaml)
    """
    core = __ci_pr_cd(shared, target)

    execute(
        core.noops_config["pipeline"][target]["ci"],
        list(cargs),
        core.noops_envs(),
        dry_run=core.is_dry_run()
    )

@pipeline.command(name='pr')
@click.pass_obj
@click.argument('target', nargs=1, required=True)
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def pull_request(shared, target, cargs):
    """pull request

    TARGET refers to pipeline.<TARGET> (noops.yaml)
    """
    core = __ci_pr_cd(shared, target)

    execute(
        core.noops_config["pipeline"][target]["pr"],
        list(cargs),
        core.noops_envs(),
        dry_run=core.is_dry_run()
    )

@pipeline.command(name='cd')
@click.pass_obj
@click.argument('target', nargs=1, required=True)
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def continuous_delivery(shared, target, cargs):
    """continuous delivery

    TARGET refers to pipeline.<TARGET> (noops.yaml)
    """
    core = __ci_pr_cd(shared, target)

    execute(
        core.noops_config["pipeline"][target]["cd"],
        list(cargs),
        core.noops_envs(),
        dry_run=core.is_dry_run()
    )

@pipeline.command()
@click.pass_obj
@click.option('--default',
    help='default deployment [DEPRECATED]', is_flag=True)
@click.argument('target', nargs=1, required=True, default="default")
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def deploy(shared, default, target, cargs): # pylint: disable=unused-argument
    """continuous deployment

    TARGET refers to pipeline.deploy.<TARGET> [default: default]
    """
    core = create_noops_instance(shared)

    if default and target != "default":
        raise click.BadArgumentUsage(
            "--default is deprecated. You can NOT use --default and a target with something " \
            f"else than default. Current target value is '{target}'"
        )

    targets = list(core.noops_config["pipeline"]["deploy"].keys())

    if target not in targets:
        raise click.BadArgumentUsage(
            "target '{}' is invalid (accepted: {})".format( # pylint: disable=consider-using-f-string
                target,
                "|".join(targets)
            )
        )

    pipeline_deploy(core, target, list(cargs))
