"""
noopsctl assist jsonschema
"""

# Copyright 2022 Croix Bleue du Québec

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
import errno
import os
import shutil
import click
from . import cli
from ..utils import resources

@cli.group()
def assist():
    """assistance for some components"""

@assist.command()
@click.option('-o', '--output', help='write the schema to a file', type=click.Path())
def jsonschema(output):
    """reference JSON Schema for noops.yaml"""
    output_path = Path(output) if output else None

    if output_path and output_path.exists():
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), output)

    with resources.schema_path_ctx() as schema_path:
        if output_path is not None:
            shutil.copyfile(schema_path, output_path)
        else:
            click.echo(schema_path.read_text(encoding='UTF-8'))
