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

from pathlib import Path
import click
from ..targets import Targets
from ..projects import Projects
from ..typing.targets import TargetKind, Cluster
from ..typing.versions import VersionKind
from ..typing.projects import ProjectKind
from ..typing.projectplans import ProjectPlanKind
from ..utils.io import read_yaml, json2yaml, write_raw
from ..errors import VerifyFailure
from . import cli

@cli.group(name="x")
def exp():
    """experimental"""

@exp.group()
def targets():
    """targets APIs"""

@targets.command(name="plan")
@click.option('-c', '--clusters', help='clusters configuration', required=True, metavar='YAML')
@click.option('-t', '--target', help='target kind configuration', required=True, metavar='YAML')
@click.option('-o', '--output', help='store output', type=click.Path())
def target_plan(clusters, target, output):
    """Create a target plan"""

    clusters_obj = read_yaml(clusters)
    ktarget = TargetKind.model_validate(read_yaml(target))

    targets_core = Targets(clusters_obj)
    target_yaml = json2yaml(targets_core.plan(ktarget).json())

    if output is None:
        click.echo(target_yaml)
    else:
        write_raw(output, target_yaml)

@exp.group()
def versions():
    """versions APIs"""

@versions.command()
@click.option('-k', '--kind',
    help='version kind file', required=True, metavar='YAML', type=click.Path())
def verify(kind):
    """check version settings"""

    version: VersionKind = VersionKind.model_validate(
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
    """projects APIs"""

@projects.command(name="plan")
@click.option('-c', '--clusters',
    help='clusters configuration', required=True, type=click.Path(), metavar='YAML')
@click.option('-t', '--targets',
    help='target kind configuration', required=True, type=click.Path(), metavar='YAML')
@click.option('-v', '--versions',
    help='version kind file', required=True, type=click.Path(), metavar='YAML')
@click.option('-p', '--projects',
    help='project kind file', required=True, type=click.Path(), metavar='YAML')
@click.option('-o', '--output', help='store output', type=click.Path())
def project_plan(clusters, targets, versions, projects, output): # pylint: disable=redefined-outer-name
    """Create an execution plan"""

    clusters_obj = [ Cluster.model_validate(i) for i in read_yaml(clusters) ]
    targets_obj = TargetKind.model_validate(read_yaml(targets))
    versions_obj = VersionKind.model_validate(read_yaml(versions))
    projects_obj = ProjectKind.model_validate(read_yaml(projects))

    plan = Projects.plan(
        clusters_obj,
        targets_obj,
        versions_obj,
        projects_obj)

    plan_yaml = json2yaml(plan.json(by_alias=True, exclude_none=True))

    if output is None:
        click.echo(plan_yaml)
    else:
        write_raw(output, plan_yaml)

@projects.command(name="create")
@click.option('-n', '--namespace', help='namespace scope', required=True)
@click.option('-r', '--release', help='release name', required=True)
@click.option('-c', '--chart', help='chart name', required=True)
@click.option('-e', '--env', help='Environment', default='dev', show_default=True, required=True)
@click.option('-p', '--envs',
    help='extra environment variables (KEY=VALUE)', multiple=True)
@click.option('-o', '--output', help='store output', type=click.Path())
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [CARGS]]")
def project_create(namespace, release, chart, env, envs, output, cargs): # pylint: disable=too-many-function-args
    """
    Create a new project

    CARGS will be used by helm install later
    """

    # build pre-procesing environment variables
    extra_envs = {}
    for extra_env in envs:
        index = extra_env.find("=")
        if index == -1:
            raise click.BadOptionUsage("envs", "only KEY=VALUE are accepted !")
        key = extra_env[:index]
        value = extra_env[index+1:]
        extra_envs[key]=value

    kproject = Projects.create(
        namespace,
        release,
        chart,
        env,
        list(cargs),
        extra_envs if len(envs) > 0 else None
    )

    kproject_yaml = json2yaml(kproject.json(by_alias=True, exclude_none=True))

    if output is None:
        click.echo(kproject_yaml)
    else:
        write_raw(output, kproject_yaml)

@projects.command(name="apply")
@click.pass_obj
@click.option('-p', '--plan', help='project plan', required=True, type=click.Path(), metavar='YAML')
@click.option('-c', '--previous-plan',
    help='previously deployed project plan', type=click.Path(), metavar='YAML')
@click.option('-z', '--pre-processing-path',
    help='Pre-processing scripts/binaries path', type=click.Path(), required=True)
def project_apply(shared, plan, previous_plan, pre_processing_path):
    """execute a project plan"""

    kprojectplan = ProjectPlanKind.model_validate(read_yaml(plan))
    kprevious = ProjectPlanKind.model_validate(read_yaml(previous_plan)) \
                if previous_plan is not None else None

    Projects().apply(
        kprojectplan,
        Path(pre_processing_path).resolve(),
        dry_run=shared["dry_run"],
        kpreviousplan=kprevious
    )

@projects.command(name="cluster-apply")
@click.pass_obj
@click.option('-p', '--project',
    help='project kind', required=True, type=click.Path(), metavar='YAML')
@click.option('-c', '--previous-project',
    help='previously deployed project kind', type=click.Path(), metavar='YAML')
@click.option('-z', '--pre-processing-path',
    help='Pre-processing scripts/binaries path', type=click.Path(), required=True)
def project_inapply(shared, project, previous_project, pre_processing_path):
    """Reconciliation in selected cluster"""

    kproject = ProjectKind.model_validate(read_yaml(project))
    kprevious = ProjectKind.model_validate(read_yaml(previous_project)) \
                if previous_project is not None else None

    Projects().apply_incluster(
        kproject,
        Path(pre_processing_path).resolve(),
        shared["dry_run"],
        kprevious=kprevious
    )

@projects.command(name="cluster-delete")
@click.pass_obj
@click.option('-p', '--project',
    help='project kind', required=True, type=click.Path(), metavar='YAML')
def project_indelete(shared, project):
    """Delete everything controlled by this project in selected cluster"""

    kproject = ProjectKind.model_validate(read_yaml(project))

    Projects().delete_incluster(kproject, shared["dry_run"])
