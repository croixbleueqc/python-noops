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
from ..projects import Projects
from ..typing.targets import TargetKind, Cluster
from ..typing.versions import VersionKind
from ..typing.projects import ProjectKind
from ..utils.io import read_yaml, json2yaml
from ..errors import VerifyFailure
from . import cli

@cli.group(name="x")
def exp():
    """experimental"""

@exp.group()
def targets():
    """targets Api"""

@targets.command(name="plan")
@click.option('-c', '--clusters', help='clusters configuration', required=True, metavar='YAML')
@click.option('-k', '--kind', help='target kind configuration', required=True, metavar='YAML')
def target_plan(clusters, kind):
    """Generate and show an execution plan"""

    clusters_obj = read_yaml(clusters)
    kind_obj = TargetKind.parse_obj(read_yaml(kind))

    targets_core = Targets(clusters_obj)
    click.echo(
        json2yaml(targets_core.plan(kind_obj).json())
    )

@exp.group()
def versions():
    """versions Api"""

@versions.command()
@click.option('-k', '--kind',
    help='version kind file', required=True, metavar='YAML', type=click.Path())
def verify(kind):
    """check version settings"""

    version: VersionKind = VersionKind.parse_obj(
        read_yaml(kind)
    )

    try:
        version.verify()
    except VerifyFailure as failure:
        click.echo(f"ERROR: {failure}")
        return

    click.echo("OK")

@exp.group()
def projects():
    """projects Api"""

@projects.command(name="plan")
@click.option('-c', '--clusters', help='clusters configuration', required=True, type=click.Path())
@click.option('-t', '--targets', help='target kind configuration', required=True, type=click.Path())
@click.option('-v', '--versions', help='version kind file', required=True, type=click.Path())
@click.option('-p', '--projects', help='project kind file', required=True, type=click.Path())
def project_plan(clusters, targets, versions, projects): # pylint: disable=redefined-outer-name
    """Generate and show an execution plan"""

    clusters_obj = [ Cluster.parse_obj(i) for i in read_yaml(clusters) ]
    targets_obj = TargetKind.parse_obj(read_yaml(targets))
    versions_obj = VersionKind.parse_obj(read_yaml(versions))
    projects_obj = ProjectKind.parse_obj(read_yaml(projects))

    plan = Projects.plan(
        clusters_obj,
        targets_obj,
        versions_obj,
        projects_obj)

    click.echo(
        json2yaml(plan.json(by_alias=True,  exclude_unset=True, exclude_none=True))
    )

@projects.command(name="create")
@click.option('-c', '--chart', help='chart keyword', required=True)
@click.option('-e', '--env', help='Environment', default='dev', show_default=True, required=True)
@click.option('-p', '--envs',
    help='Pre-processing environment variables (KEY=VALUE)', multiple=True)
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def project_create(chart, env, envs, cargs):
    """
    Create a new project

    CARGS will be used by helm install later
    """

    # build pre-procesing environment variables
    pre_processing_envs = {}
    for pre_processing_env in envs:
        index = pre_processing_env.find("=")
        if index == -1:
            raise click.BadOptionUsage("envs", "only KEY=VALUE are accepted !")
        key = pre_processing_env[:index]
        value = pre_processing_env[index+1:]
        pre_processing_envs[key]=value

    Projects.create(
        chart,
        env,
        list(cargs),
        pre_processing_envs if len(envs) > 0 else None
    )
