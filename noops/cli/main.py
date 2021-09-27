"""
noopsctl (cli composition)
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

import noops.cli.version    # pylint: disable=unused-import
import noops.cli.output     # pylint: disable=unused-import
import noops.cli.pipeline   # pylint: disable=unused-import
import noops.cli.local      # pylint: disable=unused-import
from . import cli           # pylint: disable=unused-import
