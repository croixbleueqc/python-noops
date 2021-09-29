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
import subprocess
import shutil
import re
from typing import List
import yaml
from .. import helper

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
        Create values files based on:
        - package.helm.parameters
        - package.helm.targets-parameters
        """
        logging.info("Creating values files")

        self._create_values(
            self.core.noops_config["package"]["helm"]["parameters"],
            "values"
        )

        for target, parameters in \
            self.core.noops_config["package"]["helm"].get("targets-parameters", {}).items():
            if parameters is None:
                continue

            self._create_values(
                parameters,
                f"target-{target}"
            )

    def _create_values(self, parameters: dict, prefix: str):
        """
        Create values files based on package.helm.parameters
        """

        for profile, config in parameters.items():
            values_name = f"{prefix}-{profile}.yaml"
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

    def create_package(self, app_version: str, revision: str,
        description: str, name: str, values: str):
        """
        Create a NoOps Helm Package
        """

        # Compute missing parameters values
        if app_version is None:
            app_version = "sha-" + \
                subprocess.run(
                    "git rev-parse --short=7 HEAD",
                    shell=True, check=True, capture_output=True
                ).stdout.decode().strip()

        if description is None:
            description = subprocess.run(
                'git log --pretty=format:"%s" --no-decorate -n 1 HEAD',
                shell=True, check=True, capture_output=True
            ).stdout.decode().strip()

        if name is None:
            name = os.path.split(
                os.path.abspath(self.core.product_path)
            )[1]

        # Chart.yaml
        chart_file = os.path.join(self.core.noops_config["package"]["helm"]["chart"], "Chart.yaml")
        chart = helper.read_yaml(chart_file)

        # Extract main chart version (keep only what is before + char)
        version = chart["version"].split("-")[0]

        chart["version"] = f"{version}-{revision}"
        chart["appVersion"] = app_version
        chart["description"] = description
        chart["name"] = name

        chart_keywords: List[str] = chart.get("keywords", [])
        kw1 = f"{name}--+{app_version}"
        kw2 = f"{name}-{version}-+{app_version}"
        kw3 = f"{name}-{version}-{revision}+{app_version}"

        for keyword in (kw1, kw2, kw3):
            if keyword not in chart_keywords:
                chart_keywords.append(keyword)
        chart["keywords"] = chart_keywords

        logging.info('Creating NoOps Helm Package: %s-%s', name, chart["version"])

        # Values.yaml
        chart_values_file = os.path.join(
            self.core.noops_config["package"]["helm"]["chart"], "values.yaml"
        )
        chart_values = helper.read_yaml(chart_values_file)

        # Values from parameters
        override_values = helper.read_yaml(values)

        # Merge
        chart_values = helper.deep_merge(chart_values, override_values)

        # Store
        if self.core.dryrun:
            logging.info("Generated Chart.yaml")
            print(yaml.dump(chart, indent=helper.DEFAULT_INDENT))
            logging.info("Generated Values.yaml")
            print(yaml.dump(chart_values, indent=helper.DEFAULT_INDENT))
        else:
            helper.write_yaml(chart_file, chart)
            helper.write_yaml(chart_values_file, chart_values)

            subprocess.run(
                "helm package {} -d {}".format( # pylint: disable=consider-using-f-string
                    self.core.noops_config["package"]["helm"]["chart"],
                    self.core.workdir
                ),
                shell=True,
                check=True
            )

    def push(self, directory, url):
        """
        Copy package in a directory and index it
        """

        # Chart.yaml
        chart_file = os.path.join(self.core.noops_config["package"]["helm"]["chart"], "Chart.yaml")
        chart = helper.read_yaml(chart_file)

        package = chart["name"] + "-" + chart["version"] + ".tgz"

        shutil.copy(
            os.path.join(
                self.core.workdir,
                package
            ),
            directory
        )

        subprocess.run(
            f"helm repo index {directory} --url {url}",
            shell=True,
            check=True
        )
