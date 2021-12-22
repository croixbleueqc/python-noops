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
from typing import List, Optional

def execute(cmd: str, args: List[str] = None,
    extra_envs: dict = None, product_path: str = None,
    dry_run: bool = False, shell: bool = False,
    capture_output: bool = False) -> Optional[subprocess.CompletedProcess]:
    """
    Execute a command.

    The command needs to have execution permission for the running user.
    """
    if extra_envs is None:
        extra_envs = {}
    if args is None:
        args = []

    custom_envs = {**os.environ, **extra_envs}

    cmd_str = "{} {}".format( # pylint: disable=consider-using-f-string
        cmd,
        " ".join(args)
    )
    logging.debug("execute: %s", cmd_str)

    if dry_run:
        return

    done = subprocess.run(
        [cmd] + args if not shell else cmd_str,
        shell=shell,
        check=True,
        env=custom_envs,
        cwd=product_path or os.getcwd(),
        capture_output=capture_output
    )

    if capture_output:
        return done

def get_stdout(done: subprocess.CompletedProcess) -> str:
    """
    Return the captured standard output
    """
    return done.stdout.decode().strip()
