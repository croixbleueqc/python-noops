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
from typing import List, Union, Optional
from ..typing.targets import TargetsEnum
from ..typing.profiles import ProfileEnum
from ..typing.charts import ChartKind
from ..typing.projects import ProjectKind, InstallSpec
from ..typing.versions import Spec as VersionSpec, OneSpec, MultiSpec
from ..utils.external import execute, execute_from_shell, get_stdout_from_shell
from ..utils.io import read_yaml
from ..utils.transformation import label_rfc1035
from ..targets import Targets
from ..profiles import Profiles
from ..package.helm import Helm
from ..errors import ChartNotFound
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
            raise ChartNotFound(keyword)

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

    def upgrade(self, namespace: str, release: str, chart: str, env: str, # pylint: disable=too-many-arguments,too-many-locals
        pre_processing_path: Path, profiles: List[ProfileEnum], cargs: List[str],
        extra_envs: dict = None, target: TargetsEnum = None):
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
            values_args = Helm.helm_values_args(env, dst)
            values_args += Targets.helm_targets_args(
                chartkind.spec.package.supported.target_classes, target, env, dst)

            # pre-processing
            # args to pass: -e {env} -f values1.yaml -f valuesN.yaml
            for pre_processing in chartkind.spec.package.helm.preprocessing:
                execute(
                    os.fspath(pre_processing_path / pre_processing),
                    [ "-e", env ] + values_args,
                    extra_envs=extra_envs,
                    product_path=os.fspath(dst),
                    dry_run=self.dry_run
                )

            # Profiles
            values_args += Profiles.helm_profiles_args(
                chartkind.spec.package.supported.profile_classes, profiles, dst)

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

    def reconciliation(self, kproject: ProjectKind, pre_processing_path: Path):
        """
        Upgrade all versions and clean up

        TODO: compare with previous status to cleanup orphan releases
        """

        versions: VersionSpec = kproject.spec.versions
        if versions is None:
            return

        if versions.one is not None:
            self._reconciliation_upgrade(
                kproject.metadata.namespace,
                kproject.metadata.name,
                kproject.spec.package.install,
                versions.one,
                pre_processing_path
            )

        if versions.multi is not None:
            canary_versions = []
            for version in versions.multi:
                if version.weight is not None:
                    canary_versions.append(version)

                self._reconciliation_upgrade(
                    kproject.metadata.namespace,
                    f"{kproject.metadata.name}-{version.app_version}",
                    kproject.spec.package.install,
                    version,
                    pre_processing_path,
                    cargs=self._helm_canary_weight(
                        settings.DEFAULT_PKG_HELM_CANARY_KEY + ".weight",
                        version.weight
                    )
                )

            # Canary endpoints ?
            if len(canary_versions) > 0:
                version = canary_versions[-1] # TODO: Document it !
                self._reconciliation_upgrade(
                    kproject.metadata.namespace,
                    kproject.metadata.name,
                    kproject.spec.package.install,
                    version,
                    pre_processing_path,
                    override_profiles=[ProfileEnum.DEFAULT, ProfileEnum.CANARY_ENDPOINTS_ONLY],
                    cargs=self._helm_canary_versions(
                        settings.DEFAULT_PKG_HELM_CANARY_KEY + ".instances",
                        canary_versions
                    )
                )

    @classmethod
    def _helm_canary_weight(cls, key: str, weight: Optional[int]) -> List[str]:
        """
        helm option to supply the weight used for this release/instance
        """
        if weight is None:
            return []

        return [
            "--set",
            f"{key}={weight}"
        ]

    @classmethod
    def _helm_canary_versions(cls, key:str,
        versions: List[Union[OneSpec, MultiSpec]]) -> Optional[List[str]]:
        """
        helm options to supply canary versions involved (app_version and weight)

        --set key[index].app_version=versions[index].app_version \
        --set key[index].weight=versions[index].weight
        """
        args=[]
        for index, version in enumerate(versions):
            args.append("--set")
            args.append(f"{key}[{index}].app_version={version.app_version}")
            args.append("--set")
            args.append(f"{key}[{index}].weight={version.weight}")

        return args if len(args) > 0 else None

    def _reconciliation_upgrade(self, namespace: str, release: str, # pylint: disable=too-many-arguments
        spec: InstallSpec, version: Union[OneSpec, MultiSpec],
        pre_processing_path: Path,
        override_profiles: List[ProfileEnum] = None, cargs: List[str] = None):
        """
        Run upgrade
        """
        chart_keyword = "{}-{}+{}+{}".format( # pylint: disable=consider-using-f-string
            spec.chart,
            version.build or '',
            version.version or '',
            version.app_version
        )

        # arguments
        args = cargs or []
        args.extend(spec.args or [])
        args.extend(version.args or [])

        # profiles
        profiles = override_profiles or version.profiles
        if spec.services_only:
            profiles.append(ProfileEnum.SERVICES_ONLY)

        self.upgrade(
            namespace,
            label_rfc1035(release),
            chart_keyword,
            spec.env,
            pre_processing_path,
            profiles,
            args,
            spec.envs,
            spec.target
        )
