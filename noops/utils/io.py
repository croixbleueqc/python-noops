"""
Utils: Input/Output

Supported format:
- Yaml
- Json
- Text (raw)
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

import json
import os
from pathlib import Path, PosixPath, WindowsPath
from typing import Union
import yaml
from ..settings import DEFAULT_INDENT

# Json and Yaml representation for Path

class PathEncoder(json.JSONEncoder):
    """
    Custom Encoder for Path (json)
    """
    def default(self, o):
        if isinstance(o, Path):
            return os.fspath(o)
        return json.JSONEncoder.default(self, o) # pragma: no cover

def path_representer(dumper: yaml.Dumper, data):
    """
    Custom Encoder for Path (yaml)
    """
    return dumper.represent_scalar('!path', os.fspath(data))

def path_constructor(loader: yaml.Loader, node):
    """
    Custom Loader for !path
    """
    return Path(loader.construct_scalar(node))

yaml.Dumper.add_representer(PosixPath, path_representer)
yaml.Dumper.add_representer(WindowsPath, path_representer)
yaml.SafeLoader.add_constructor('!path', path_constructor)

# IO functions

def read_yaml(file_path: Union[str, Path]) -> dict: # pragma: no cover
    """
    Read a yaml file
    """
    with open(file_path, "r", encoding="UTF-8") as file:
        noops = yaml.load(file, Loader=yaml.SafeLoader)

    return noops

def write_yaml(file_path: Union[str, Path], content: dict, indent=DEFAULT_INDENT,
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

def read_json(file_path: Union[str, Path]) -> dict: # pragma: no cover
    """
    Read a json file
    """
    with open(file_path, "r", encoding="UTF-8") as file:
        content = json.load(file)

    return content

def write_json(file_path: Union[str, Path], content: dict, indent=DEFAULT_INDENT,
    dry_run: bool = False):
    """
    Write as a json file
    """
    if dry_run:
        print(json.dumps(content, indent=indent, cls=PathEncoder))
        return

    with open(file_path, "w", encoding="UTF-8") as file:
        json.dump(content, fp=file, indent=indent, cls=PathEncoder)

def write_raw(file_path: Union[str, Path], content: str, dry_run: bool = False):
    """
    Write as a text file
    """
    if dry_run:
        print(content)
        return

    with open(file_path, "w", encoding="UTF-8") as file:
        file.write(content)
