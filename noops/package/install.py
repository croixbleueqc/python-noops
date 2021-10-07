"""
Helm install
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
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
from ..typing.targets import TargetsEnum
from ..typing.charts import ChartKind
from ..utils.external import execute, execute_from_shell, get_stdout_from_shell
from ..utils.io import read_yaml
from ..targets import Targets
from ..errors import TargetNotSupported
from .. import settings

class HelmInstall():
    """
    Manages Helm upgrade/install and everything around that process
    """

    def __init__(self, dry_run: bool):
        self._dry_run = dry_run

    @property
    def dry_run(self) -> bool:
        """Are we in dry-run mode ?"""
        return self._dry_run

    @classmethod
    def update(cls):
        """
        Update repositories

        helm repo update
        """
        execute_from_shell("helm repo update")

    @classmethod
    def search_latest(cls, keyword: str) -> dict:
        """
        Search latest chart which meets criterias

        helm search repo ...
        """
        charts = json.loads(
            get_stdout_from_shell(
                f"helm search repo {keyword} -o json"
            )
        )
        if len(charts) == 0:
            raise ValueError()

        return charts[0]

    @classmethod
    def pull(cls, pkg: dict, dst: Path) -> Path:
        """
        Download the chart locally

        helm pull
        """
        pkg_fullname = pkg["name"]
        pkg_name = pkg_fullname.split("/")[1]
        pkg_version = pkg["version"]

        execute_from_shell(
            f"helm pull {pkg_fullname} --untar --version {pkg_version} --untardir {os.fspath(dst)}"
        )

        return dst / pkg_name

    def upgrade(self, namespace: str, release: str, chart: str, env: str, # pylint: disable=too-many-arguments
        pre_processing_path: Path, cargs: List[str],
        pre_processing_envs: dict = None, target: TargetsEnum = None):
        """
        helm upgrade {release}
            {chart}
            --install
            --namespace {namespace}
            --values values-default.yaml
            --values values-{env}.yaml
            --values values-svcat.yaml
            {cargs...}
        """

        # Get the chart
        self.update()
        pkg = self.search_latest(chart)

        logging.info("Installation of %s", str(pkg))

        with TemporaryDirectory(prefix=settings.TMP_PREFIX) as tmp:
            # Pull it
            dst = self.pull(pkg, Path(tmp))

            # noops.yaml (chart kind)
            chartkind = self._chart_kind(dst)

            # Values
            values_args = self._values_args(env, dst)
            values_args += self._targets_args(chartkind, target, env, dst)

            # pre-processing
            # args to pass: -e {env} -f values1.yaml -f valuesN.yaml
            for pre_processing in chartkind.spec.package.helm.preprocessing:
                execute(
                    os.fspath(pre_processing_path / pre_processing),
                    [ "-e", env ] + values_args,
                    extra_envs=pre_processing_envs,
                    product_path=os.fspath(dst),
                    dry_run=self.dry_run
                )

            # let's go !
            execute(
                "helm",
                [
                    "upgrade",
                    release,
                    os.fspath(dst),
                    "--install",
                    "--create-namespace",
                    "--namespace", namespace
                ] + values_args + cargs,
                dry_run=self.dry_run
            )

    @classmethod
    def _chart_kind(cls, dst: Path) -> ChartKind:
        """
        Read the noops.yaml from chart
        """
        return ChartKind.parse_obj(
            read_yaml(dst / settings.DEFAULT_NOOPS_FILE)
        )

    @classmethod
    def _values_args(cls, env: str, dst: Path) -> List[str]:
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

    @classmethod
    def _targets_args(cls, chartkind: ChartKind, target: TargetsEnum, env: str,
        dst: Path) -> List[str]:
        """
        Create targets arguments to use
        """
        targets_args=[]

        if target is None:
            return targets_args

        # check compatibility
        if not Targets.is_compatible(
            target,
            chartkind.spec.package.supported.target_classes):
            raise TargetNotSupported(target)

        for values in ("-default", f"-{env}", ""):
            values_file = dst / "noops" / f"target-{target.value}{values}.yaml"
            if values_file.exists():
                targets_args.append("-f")
                targets_args.append(os.fspath(values_file))

        return targets_args
