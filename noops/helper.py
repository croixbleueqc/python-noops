"""
Helper

Defines some standard functions or default variables
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

import yaml
import json
import os
from functools import reduce
from copy import deepcopy

DEFAULT_INDENT=2
DEFAULT_NOOPS_FILE="noops.yaml"
DEFAULT_WORKDIR="noops_workdir"

def read_yaml(file: str) -> dict:
    """
    Read a yaml file
    """
    with open(file, "r") as f:
        noops = yaml.load(f, Loader=yaml.SafeLoader)

    return noops

def write_yaml(file: str, content: dict, indent=DEFAULT_INDENT):
    """
    Write as a yaml file
    """
    with open(file, "w") as f:
        yaml.dump(content, stream=f, indent=indent)

def write_json(file: str, content: dict, indent=DEFAULT_INDENT):
    """
    Write as a json file
    """
    with open(file, "w") as f:
        json.dump(content, fp=f, indent=indent)

def write_raw(file: str, content: str):
    """
    Write as a text file
    """
    with open(file, "w") as f:
        f.write(content)

def deep_merge(dict_base: dict, dict_custom: dict) -> dict:
    """
    Recursive merge in a dict

    There isn't any deep merge for an array. An array is replaced.
    """
    result = deepcopy(dict_base)
    for key, value in dict_custom.items():
        if isinstance(value, dict):
            node = result.setdefault(key, {})
            mergedNode = deep_merge(node, value)
            result[key] = mergedNode
        else:
            result[key] = value

    return result

def merge(devops: dict, product: dict) -> dict:
    """
    Merge 2 dicts.

    product dict overrides devops dict
    """
    # Order is important inside the list
    return reduce(deep_merge, [{}, devops, product])
