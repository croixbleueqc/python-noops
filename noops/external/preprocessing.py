"""
Provide an abstraction code to implement a pre-processing script
Pre-processing can apply some changes to an helm chart before helm templating
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

from typing import List
from pathlib import Path
import click

class PreProcessing:
    """
    Pre-Processing Abstract Class
    """
    def apply(self, env: str, chart: Path, values: List[Path], kustomize: List[Path]):
        """
        Apply pre-processing actions to Helm files
        """
        raise NotImplementedError()

    def run(self):
        """Start the command line"""

        @click.group(
            context_settings=dict(help_option_names=["-h", "--help"]),
            invoke_without_command=True
        )
        @click.option('-e', '--env', help='environment', required=True)
        @click.option('-c', '--chart',
            help='chart path', required=True, type=click.Path(exists=True))
        @click.option('-f', '--values',
            help='values.yaml files', type=click.Path(exists=True), required=True, multiple=True)
        @click.option('-k', '--kustomize',
            help='kustomize path', type=click.Path(), multiple=True, default=[])
        def cli(env, chart, values, kustomize):
            """Pre-processing Helm files before templating"""

            self.apply(
                env,
                Path(chart),
                [Path(i) for i in values],
                [Path(i) for i in kustomize]
            )

        cli() # pylint: disable=no-value-for-parameter
