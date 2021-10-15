"""
Utils: Transformation
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

import string
import re

def label_rfc1035(label: str) -> str:
    """
    The labels must follow the rules for ARPANET host names.  They must
    start with a letter, end with a letter or digit, and have as interior
    characters only letters, digits, and hyphen.  There are also some
    restrictions on the length.  Labels must be 63 characters or less.
    """
    accepted = string.ascii_lowercase + string.digits + "-"
    transform = label.lower() # lower case only
    transform = re.sub(f'[^{accepted}]', '-', transform) # replace unaccepted chars
    transform = transform[:63] # 63 chars maximum

    while transform[-1] == "-":
        transform = transform[:-1]

    return transform
