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
import click
from . import cli, create_noops_instance
from ..package.prepare import prepare
from ..package.serve import serve_forever
from ..package.helm import Helm

@cli.group()
@click.pass_context
def package(ctx):
    """manage packages"""
    if ctx.invoked_subcommand != "serve" and \
        ctx.obj['product'] is None:
        raise click.BadOptionUsage("product","Missing option '-p' / '--product'.", ctx=ctx.parent)

@package.command()
@click.pass_obj
@click.option('-a', '--app-version', help='Application version')
@click.option('-r', '--revision', help='Build number', required=True, type=click.INT)
@click.option('-d', '--description', help='One line description about this new version')
@click.option('-c', '--chart-name', help='Override chart name auto detection')
@click.option('-f', '--values',
    help='override image/tag/... in chart values.yaml', required=True, type=click.Path())
def create(shared, app_version, revision, description, chart_name, values): # pylint: disable=too-many-arguments
    """create a package"""
    values_file = os.path.abspath(values)

    core = create_noops_instance(shared)
    helm = Helm(core, chart_name)
    prepare(core, helm)
    helm.create_package(app_version, revision, description, values_file)

@package.command()
@click.pass_obj
@click.option('--directory', help='repository directory', type=click.Path(), required=True)
@click.option('--url', help='url of chart repository',
    show_default=True, default='http://0.0.0.0:8000', type=click.STRING)
def push(shared, directory, url):
    """push to a repository"""

    directory_abs = os.path.abspath(directory)
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
