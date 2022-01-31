"""
noopsctl package create
noopsctl package push
noopsctl package serve
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
import errno
from pathlib import Path
import click
from . import cli, create_noops_instance
from ..package.prepare import prepare
from ..package.serve import serve_forever
from ..package.helm import Helm
from ..package.install import HelmInstall
from ..typing.targets import TargetsEnum
from ..typing.profiles import ProfileEnum

@cli.group()
@click.pass_context
def package(ctx):
    """manage packages"""
    if ctx.invoked_subcommand not in ("serve", "install") and \
        ctx.obj['product'] is None:
        raise click.BadOptionUsage("product","Missing option '-p' / '--product'.", ctx=ctx.parent)

@package.command()
@click.pass_obj
@click.option('-a', '--app-version', help='Application version')
@click.option('-b', '--build', help='Build number', required=True)
@click.option('-d', '--description', help='One line description about this new version')
@click.option('-c', '--chart-name', help='Override chart name auto detection')
@click.option('-f', '--values',
    help='override image/tag/... in chart values.yaml', type=click.Path())
def create(shared, app_version, build, description, chart_name, values): # pylint: disable=too-many-arguments
    """create a package"""
    values_file = None if values is None else Path(values).resolve()

    core = create_noops_instance(shared)
    helm = Helm(core, chart_name)
    prepare(core, helm)
    helm.create_package(app_version, build, description, values_file)

@package.command()
@click.pass_obj
@click.option('-d', '--directory', help='repository directory', type=click.Path(), required=True)
@click.option('-u', '--url', help='url of chart repository',
    show_default=True, default='http://0.0.0.0:8000', type=click.STRING)
def push(shared, directory, url):
    """push to a repository"""

    directory_abs = Path(directory).resolve()
    core = create_noops_instance(shared)
    Helm(core).push(directory_abs, url)

@package.command()
@click.option('-d', '--directory',
    help='alternate directory [default:current directory]', metavar='DIRECTORY', type=click.Path())
@click.option('-b', '--bind',
    help='alternate bind address [default: 0.0.0.0]', metavar='ADDRESS', type=click.STRING)
@click.option('-p', '--port',
    help='alternate port', type=click.INT, default=8000, show_default=True)
def serve(directory, bind, port): # pylint: disable=invalid-name
    """Serve packages (not recommended for production)"""
    serve_forever(directory, bind, port)

@package.group()
def install():
    """
    install a package
    """

@install.command(name='helm')
@click.pass_obj
@click.option('-n', '--namespace', help='namespace scope')
@click.option('-r', '--release', help='release name')
@click.option('-c', '--chart', help='chart keyword or local tgz package')
@click.option('-e', '--env', help='Environment', default='dev', show_default=True)
@click.option('-z', '--pre-processing-path',
    help='Pre-processing scripts/binaries path', type=click.Path(), required=True)
@click.option('-t', '--target',
    type=click.Choice(TargetsEnum.list(), case_sensitive=True))
@click.option('-p', '--profile', multiple=True, default=['default'],
    type=click.Choice(ProfileEnum.list(), case_sensitive=True))
@click.argument('cargs', nargs=-1, type=click.UNPROCESSED, metavar="[-- [-h] [CARGS]]")
def install_helm(shared, namespace, release, chart, env, # pylint: disable=too-many-arguments
    pre_processing_path, target, profile, cargs):
    """
    install a NoOps helm package

    CARGS are passed directly to helm
    """

    profiles = [ProfileEnum(i) for i in profile]

    # Chart can be a string keyword or a Path to tgz file
    _chart = Path(chart)
    if _chart.suffix in (".tgz", ".gz"):
        if not _chart.exists():
            raise FileNotFoundError(
                    errno.ENOENT,
                    os.strerror(errno.ENOENT),
                    _chart
                )
        chart = _chart

    helm = HelmInstall(shared["dry_run"])
    helm.upgrade(
        namespace,
        release,
        chart,
        env,
        Path(pre_processing_path).resolve(),
        profiles,
        list(cargs),
        target=TargetsEnum(target) if target is not None else None)
