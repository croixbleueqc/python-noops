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
from pathlib import Path
import shutil
import re
from typing import Optional, List
from .. import settings
from ..utils.external import execute, get_stdout_from_shell, execute_from_shell
from ..utils import containers
from ..utils import io
from ..noops import NoOps

class Helm():
    """
    Manages Helm Chart
    """
    re_noops_chart = re.compile("{{noops:chart:(.*):(.*)}}")

    def __init__(self, core: NoOps, chart_name: str = None):
        self._core = core
        self._config = core.noops_config["package"]["helm"]

        # Chart name
        if chart_name is None:
            # Compute chart name
            self._chart_name = os.path.split(os.getcwd())[1]
        else:
            self._chart_name = chart_name

        logging.info("using chart name '%s'", self.chart_name)

    @property
    def config(self) -> dict:
        """config property"""
        return self._config

    @property
    def core(self) -> NoOps:
        """core property"""
        return self._core

    @property
    def chart_name(self) -> str:
        """chart property"""
        return self._chart_name

    def include(self, macro, nindent=None, root="."):
        """Include chart directive

        {{- include "chart.macro" . }}
        """
        value = f'''include "{self.chart_name}.{macro}" {root}'''

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

        self.get_values_path().mkdir(parents=True, exist_ok=True)

    def create_values(self):
        """
        Create values files based on:
        - package.helm.parameters
        - package.helm.targets-parameters
        - package.helm.definitions.targets (or default settings)
        - package.helm.definitions.profiles (or default settings)
        """
        logging.info("Creating values files")

        self.create_values_directory()

        # "regular" values
        self._create_values(
            self.config["parameters"],
            "values"
        )

        # targets
        for target, parameters in \
            self.config.get("targets-parameters", {}).items():
            if parameters is None:
                continue

            self._create_values(
                parameters,
                f"target-{target}"
            )

        self._create_values(
            self.config.get("definitions", settings.DEFAULT_PKG_HELM_DEFINITIONS)["targets"],
            "target"
        )

        # profiles
        self._create_values(
            self.config.get("definitions", settings.DEFAULT_PKG_HELM_DEFINITIONS)["profiles"],
            "profile"
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

    def get_values_path(self, values_filename: str = None) -> Path:
        """
        Directory where to store values.yaml files
        """
        if values_filename is None:
            return self.config["values"]

        return self.config["values"] / values_filename

    def create_package(self, app_version: str, build: str, # pylint: disable=too-many-arguments
        description: str, values: Optional[Path]):
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

        # Chart.yaml
        chart_file = self.config["chart"] / "Chart.yaml"
        chart = io.read_yaml(chart_file)

        # Extract main chart version (keep only what is after + char)
        version = chart["version"].split("+")
        version = version[1] if len(version) == 2 else version[0]

        chart["version"] = f"{build}+{version}"
        chart["appVersion"] = app_version
        chart["description"] = description
        chart["name"] = self.chart_name

        if chart.get("keywords") is None:
            chart["keywords"] = []

        for keyword in (
            f"{self.chart_name}-++{app_version}",
            f"{self.chart_name}-+{version}+{app_version}",
            f"{self.chart_name}-{build}+{version}+{app_version}"):
            chart["keywords"].append(keyword)

        logging.info('Creating NoOps Helm Package: %s-%s', self.chart_name, chart["version"])

        logging.info("Generated Chart.yaml")
        io.write_yaml(chart_file, chart, dry_run=self.core.is_dry_run())

        # Values.yaml
        if values is not None:
            # Values.yaml
            chart_values_file = self.config["chart"] / "values.yaml"
            chart_values = io.read_yaml(chart_values_file)

            # Values from parameters
            override_values = io.read_yaml(values)

            # Merge
            chart_values = containers.deep_merge(chart_values, override_values)

            logging.info("Generated Values.yaml")
            io.write_yaml(chart_values_file, chart_values, dry_run=self.core.is_dry_run())

        # noops.yaml chart
        noops_chart_config = {
            "apiVersion": "noops.local/v1alpha1",
            "kind": "chart",
            "spec": {
                "package": {
                    "supported": self.core.noops_config["package"].get("supported"),
                    "helm": {
                        "pre-processing" : self.core.noops_config["package"] \
                                            .get("helm", {}).get("pre-processing", [])
                    }
                }
            }
        }
        noops_file = self.config["chart"] / settings.DEFAULT_NOOPS_FILE
        io.write_yaml(noops_file, noops_chart_config, dry_run=self.core.is_dry_run())

        execute(
            "helm",
            [
                "package",
                os.fspath(self.config["chart"]),
                "-d",
                os.fspath(self.core.workdir)
            ],
            dry_run=self.core.is_dry_run()
        )

    def push(self, directory: Path, url: str):
        """
        Copy package in a directory and index it
        """

        # Chart.yaml
        chart_file = self.config["chart"] / "Chart.yaml"
        chart = io.read_yaml(chart_file)

        package = chart["name"] + "-" + chart["version"] + ".tgz"

        shutil.copy(
            self.core.workdir / package,
            directory
        )

        execute_from_shell(f"helm repo index {directory} --url {url}")

    @classmethod
    def helm_values_args(cls, env: str, dst: Path) -> List[str]:
        """
        Select all values*.yaml files requested to install the package
        """
        # Values: Look for default, {env}, svcat
        values_args=[]
        for values in ("default", env, settings.VALUES_SVCAT):
            values_file = dst / "noops" / f"values-{values}.yaml"
            if values_file.exists():
                values_args.append("-f")
                values_args.append(os.fspath(values_file))

        return values_args
