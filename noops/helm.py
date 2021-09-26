"""
Helm

Handles helm section of noops.yaml

- Create all values files
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

import logging
import os
import re
import yaml
from . import helper

class Helm():
    """
    Manages Helm Chart
    """
    re_noops_chart = re.compile("{{noops:chart:(.*):(.*)}}")

    def __init__(self, core, chart_name: str):
        self.core = core

        # Chart name
        if chart_name is None:
            # Compute chart name
            self.chart = os.path.split(
                self.core.noops_config["package"]["helm"]["chart"]
                )[1]
        else:
            self.chart = chart_name

        logging.info("using chart name '%s'", self.chart)

    def include(self, macro, nindent=None, root="."):
        """Include chart directive

        {{- include "chart.macro" . }}
        """
        value = f'''include "{self.chart}.{macro}" {root}'''

        if nindent is not None:
            value += f' | nindent {nindent}'

        return '{{ ' + value + ' }}'

    def as_chart_template(self, source: str):
        """Transform the input string to use it in a chart template"""

        #TODO: optimize the code (avoid replace() to start from 0 each time)

        template = source.replace("'{{", "{{").replace("}}'", "}}")

        for match in Helm.re_noops_chart.finditer(source):
            template = template.replace(match[0], self.include(match[2]), 1)

        return template

    def create_values(self):
        """
        Create values files based on package.helm.parameters
        """
        logging.info("Creating values files")

        parameters: dict = self.core.noops_config["package"]["helm"]["parameters"]
        for profile, config in parameters.items():
            values_name = f"values-{profile}.yaml"
            logging.info("Creating %s", values_name)

            if self.core.dryrun:
                print(yaml.dump(config, indent=helper.DEFAULT_INDENT))
            else:
                helper.write_yaml(
                    os.path.join(
                        self.core.noops_config["package"]["helm"]["values"],
                        values_name
                    ),
                    config,
                    indent=helper.DEFAULT_INDENT
                )
