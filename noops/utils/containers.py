"""
Utils: containers functions
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

from functools import reduce
from copy import deepcopy

def deep_merge(dict_base: dict, dict_custom: dict) -> dict:
    """
    Recursive merge in a dict

    There isn't any deep merge for an array. An array is replaced.
    """
    result = deepcopy(dict_base)
    for key, value in dict_custom.items():

        if key is None:
            #pass
            print(f"NoneType key found. This is not normal!\nDEBUG dict_base:\n{dict_base}\nDEBUG dict_custom:\n{dict_custom}\nDEBUG Current value:\n{value}")
        elif result is None: 
            #pass
            print(f"NoneType result found. This is not normal!\nDEBUG dict_base:\n{dict_base}\nDEBUG dict_custom:{dict_custom}\nDEBUG Current key: {key}\nDEBUG Current value: {value}")
        elif value is None:
            #pass
            print(f"DEBUG value in deepcopy is None\nDEBUG: key: {key}, value: {value}")
        elif isinstance(value, dict):
            node = result.setdefault(key, {})
            merged_node = deep_merge(node, value)
            result[key] = merged_node
        else:
            try:
              result[key] = value
            except:
                #pass
                print("DEBUG Exception on result[key] = value\nDEBUG: key: {key}, value: {value}")

    return result

def merge(low: dict, high: dict) -> dict:
    """
    Merge 2 dicts.

    high dict overrides low dict
    """
    # Order is important inside the list
    return reduce(deep_merge, [{}, low, high])
