"""
Utils: Input/Output

Supported format:
- Yaml
- Json
- Text (raw)
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

import json
import yaml
from ..settings import DEFAULT_INDENT

def read_yaml(file_path: str) -> dict: # pragma: no cover
    """
    Read a yaml file
    """
    with open(file_path, "r", encoding="UTF-8") as file:
        noops = yaml.load(file, Loader=yaml.SafeLoader)

    return noops

def write_yaml(file_path: str, content: dict, indent=DEFAULT_INDENT,
    dry_run: bool = False):
    """
    Write as a yaml file
    """
    if dry_run:
        print(yaml.dump(content, indent=indent))
        return

    with open(file_path, "w", encoding="UTF-8") as file:
        yaml.dump(content, stream=file, indent=indent)

def json2yaml(content: str, indent=DEFAULT_INDENT) -> str: # pragma: no cover
    """
    Return as a yaml
    """
    return yaml.dump(json.loads(content), indent=indent)

def write_json(file_path: str, content: dict, indent=DEFAULT_INDENT,
    dry_run: bool = False):
    """
    Write as a json file
    """
    if dry_run:
        print(json.dumps(content, indent=indent))
        return

    with open(file_path, "w", encoding="UTF-8") as file:
        json.dump(content, fp=file, indent=indent)

def write_raw(file_path: str, content: str, dry_run: bool = False):
    """
    Write as a text file
    """
    if dry_run:
        print(content)
        return

    with open(file_path, "w", encoding="UTF-8") as file:
        file.write(content)
