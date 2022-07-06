"""
Utils: Manages internal resources
"""

# Copyright 2021-2022 Croix Bleue du Québec

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

from contextlib import contextmanager
from pathlib import Path
import importlib.resources as pkg_resources
from ..settings import SCHEMA_FILE
from .. import schema

@contextmanager
def schema_path_ctx() -> Path:
    """Context to get schema file path"""
    with pkg_resources.path(schema, SCHEMA_FILE) as schema_path:
        yield schema_path
