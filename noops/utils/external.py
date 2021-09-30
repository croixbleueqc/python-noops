"""
Utils: run external commands
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
import subprocess
import logging
from typing import List

def execute(cmd: str, args: List[str],
    extra_envs: dict = None, product_path: str = None,
    dry_run: bool = False):
    """
    Execute a command.

    The command needs to have execution permission for the running user.
    """
    if extra_envs is None:
        extra_envs = {}

    custom_envs = {**os.environ, **extra_envs}

    logging.debug("execute: %s %s", cmd, " ".join(args))

    if dry_run:
        return

    subprocess.run(
        [cmd] + args,
        shell=False,
        check=True,
        env=custom_envs,
        cwd=product_path or os.getcwd()
    )
