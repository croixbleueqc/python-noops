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
import shutil
import re
from .. import settings
from ..utils.external import execute, get_stdout_from_shell, execute_from_shell
from ..utils import containers
from ..utils import io

class Helm():
    """
    Manages Helm Chart
    """
    re_noops_chart = re.compile("{{noops:chart:(.*):(.*)}}")

    def __init__(self, core, chart_name: str = None):
        self.core = core
        self.config = core.noops_config["package"]["helm"]

        # Chart name
        if chart_name is None:
            # Compute chart name
            self.chart = os.path.split(
                self.config["chart"]
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

    def create_values_directory(self):
        """
        mkdir the values directory if it doesn't exist
        """
        if self.core.is_dry_run():
            return

        os.makedirs(self.get_values_path(), exist_ok=True)

    def create_values(self):
        """
        Create values files based on:
        - package.helm.parameters
        - package.helm.targets-parameters
        """
        logging.info("Creating values files")

        self.create_values_directory()

        self._create_values(
            self.config["parameters"],
            "values"
        )

        for target, parameters in \
            self.config.get("targets-parameters", {}).items():
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

            io.write_yaml(
                self.get_values_path(values_name),
                config,
                indent=settings.DEFAULT_INDENT,
                dry_run=self.core.is_dry_run()
            )

    def get_values_path(self, values_filename: str = None) -> str:
        """
        Directory where to store values.yaml files
        """
        if values_filename is None:
            return self.config["values"]

        return os.path.join(
            self.config["values"],
            values_filename
        )

    def create_package(self, app_version: str, revision: str, # pylint: disable=too-many-arguments
        description: str, name: str, values: str):
        """
        Create a NoOps Helm Package
        """

        # Compute missing parameters values
        if app_version is None:
            app_version = "sha-" + \
                get_stdout_from_shell("git rev-parse --short=7 HEAD")

        if description is None:
            description = get_stdout_from_shell(
                'git log --pretty=format:"%s" --no-decorate -n 1 HEAD'
            )

        if name is None:
            name = os.path.split(os.getcwd())[1]

        # Chart.yaml
        chart_file = os.path.join(self.config["chart"], "Chart.yaml")
        chart = io.read_yaml(chart_file)

        # Extract main chart version (keep only what is before + char)
        version = chart["version"].split("-")[0]

        chart["version"] = f"{version}-{revision}"
        chart["appVersion"] = app_version
        chart["description"] = description
        chart["name"] = name

        if chart.get("keywords") is None:
            chart["keywords"] = []

        for keyword in (
            f"{name}--+{app_version}",
            f"{name}-{version}-+{app_version}",
            f"{name}-{version}-{revision}+{app_version}"):
            chart["keywords"].append(keyword)

        logging.info('Creating NoOps Helm Package: %s-%s', name, chart["version"])

        # Values.yaml
        chart_values_file = os.path.join(
            self.config["chart"], "values.yaml"
        )
        chart_values = io.read_yaml(chart_values_file)

        # Values from parameters
        override_values = io.read_yaml(values)

        # Merge
        chart_values = containers.deep_merge(chart_values, override_values)

        # Store
        logging.info("Generated Chart.yaml")
        io.write_yaml(chart_file, chart, dry_run=self.core.is_dry_run())

        logging.info("Generated Values.yaml")
        io.write_yaml(chart_values_file, chart_values, dry_run=self.core.is_dry_run())

        execute(
            "helm",
            [
                "package",
                self.config["chart"],
                "-d",
                self.core.workdir
            ],
            dry_run=self.core.is_dry_run()
        )

    def push(self, directory, url):
        """
        Copy package in a directory and index it
        """

        # Chart.yaml
        chart_file = os.path.join(self.config["chart"], "Chart.yaml")
        chart = io.read_yaml(chart_file)

        package = chart["name"] + "-" + chart["version"] + ".tgz"

        shutil.copy(
            os.path.join(
                self.core.workdir,
                package
            ),
            directory
        )

        execute_from_shell(f"helm repo index {directory} --url {url}")
