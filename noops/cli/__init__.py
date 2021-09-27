"""
noopsctl (cli entrypoint)
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

import logging
import click
from noops.noops import NoOps

@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
@click.option('-p', '--product', help='product directory', metavar='path')
@click.option('-r', '--rm-cache', help='remove the workdir cache', is_flag=True, default=False)
@click.option('-v', '--verbose', help='warning (-v), info (-vv), debug (-vvv)',
    count=True, show_default='error')
@click.option('-d', '--dry-run', help='dry-run', is_flag=True)
@click.option('-s', '--show', help='show noops final configuration', is_flag=True, default=False)
def cli(ctx, verbose, **kwargs):
    """main cli entrypoint"""

    # logging
    if verbose == 0:
        level=logging.ERROR
    elif verbose == 1:
        level=logging.WARN
    elif verbose == 2:
        level=logging.INFO
    else:
        level=logging.DEBUG

    logging.basicConfig(level=level)

    if ctx.invoked_subcommand not in ("version", "targets") and \
        kwargs['product'] is None:
        raise click.BadOptionUsage("product","Missing option '-p' / '--product'.")

    ctx.ensure_object(dict)
    ctx.obj.update(kwargs)

def create_noops_instance(shared: dict) -> NoOps:
    """Create an instance of NoOps based on cli shared options"""
    return NoOps(
        shared["product"],
        None, # chart_name unused
        shared["dry_run"],
        shared["show"],
        shared["rm_cache"]
    )
