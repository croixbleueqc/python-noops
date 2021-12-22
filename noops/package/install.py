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
from ..typing.projects import ProjectKind, InstallSpec, ProjectReconciliationPlan
from ..typing.versions import OneSpec, MultiSpec
from ..utils.external import execute, get_stdout
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
        logging.info("update repositories")
        _ = execute(
            "helm",
            ["repo", "update"],
            capture_output=True
        )

    @classmethod
    def search_latest(cls, keyword: str) -> dict:
        """
        Search latest chart which meets criterias

        helm search repo ...
        """
        charts = json.loads(
            get_stdout(
                execute(
                    "helm",
                    ["search", "repo", keyword, "-o", "json"],
                    capture_output=True
                )
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

        logging.debug("pull version %s for %s", pkg_version, pkg_fullname)
        _ = execute(
            "helm",
            [
                "pull", pkg_fullname,
                "--version", pkg_version,
                "--untar", "--untardir", os.fspath(dst)
            ],
            capture_output=True
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

        logging.info(
            "Installation of %s in namespace %s (chart: %s-%s)",
            release, namespace, pkg["name"], pkg["version"]
        )

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
                _ = execute(
                    os.fspath(pre_processing_path / pre_processing),
                    [ "-e", env ] + values_args,
                    extra_envs=extra_envs,
                    product_path=os.fspath(dst),
                    dry_run=self.dry_run,
                    capture_output=True
                )

            # Profiles
            values_args += Profiles.helm_profiles_args(
                chartkind.spec.package.supported.profile_classes, profiles, dst)

            # let's go !
            _ = execute(
                "helm",
                [
                    "upgrade",
                    release,
                    os.fspath(dst),
                    "--install",
                    "--create-namespace",
                    "--namespace", namespace
                ] + values_args + cargs,
                dry_run=self.dry_run,
                capture_output=True
            )

    def uninstall(self, namespace: str, release: str):
        """
        Uninstall a release
        """
        # let's go !
        logging.info("Uninstall %s in namespace %s", release, namespace)
        _ = execute(
            "helm",
            [
                "uninstall",
                release,
                "--namespace", namespace
            ],
            dry_run=self.dry_run,
            capture_output=True
        )

    @classmethod
    def _chart_kind(cls, dst: Path) -> ChartKind:
        """
        Read the noops.yaml from chart
        """
        return ChartKind.parse_obj(
            read_yaml(dst / settings.DEFAULT_NOOPS_FILE)
        )

    def reconciliation(self, kproject: ProjectKind, kprevious: ProjectKind,
        pre_processing_path: Optional[Path] = None):
        """
        Upgrade all versions and clean up
        """

        plan = self._reconciliation_plan(kproject, kprevious)

        for version in plan.removed:
            if isinstance(version, OneSpec):
                release = kproject.metadata.name
            else:
                release = f"{kproject.metadata.name}-{version.app_version}"

            self._reconciliation_uninstall(kproject.metadata.namespace, release)

        if plan.removed_canary:
            self._reconciliation_uninstall(
                kproject.metadata.namespace,
                kproject.metadata.name
            )

        for version in plan.changed + plan.added:
            if isinstance(version, OneSpec):
                # versions.one
                self._reconciliation_upgrade(
                    kproject.metadata.namespace,
                    kproject.metadata.name,
                    kproject.spec.package.install,
                    version,
                    pre_processing_path
                )
            else:
                # one entry in versions.multi
                self._reconciliation_upgrade(
                    kproject.metadata.namespace,
                    f"{kproject.metadata.name}-{version.app_version}",
                    kproject.spec.package.install,
                    version,
                    pre_processing_path,
                    cargs=self._helm_canary_weight(
                        settings.DEFAULT_PKG_HELM_DEFINITIONS["keys"]["canary"] + ".weight",
                        version.weight
                    )
                )

        if plan.canary_versions is not None:
            version = plan.canary_versions[-1] # TODO: Document it !
            self._reconciliation_upgrade(
                kproject.metadata.namespace,
                kproject.metadata.name,
                kproject.spec.package.install,
                version,
                pre_processing_path,
                override_profiles=[ProfileEnum.DEFAULT, ProfileEnum.CANARY_ENDPOINTS_ONLY],
                cargs=self._helm_canary_versions(
                    settings.DEFAULT_PKG_HELM_DEFINITIONS["keys"]["canary"] + ".instances",
                    plan.canary_versions
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

    @classmethod
    def _reconciliation_plan(cls,
        current: ProjectKind, previous: ProjectKind) -> ProjectReconciliationPlan:
        """
        Determine what need to be changed from previous to current project definition
        """

        plan = ProjectReconciliationPlan()

        # if package definition has changed, we will need to update everything
        forced_change = (current.spec.package != previous.spec.package)

        # One
        if current.spec.versions.one != previous.spec.versions.one:
            if current.spec.versions.one is None:
                # remove
                plan.removed.append(previous.spec.versions.one)
            elif previous.spec.versions.one is None:
                # add
                plan.added.append(current.spec.versions.one)
            else:
                # change
                plan.changed.append(current.spec.versions.one)
        elif current.spec.versions.one is not None and forced_change:
            # forced change due to package definition
            plan.changed.append(current.spec.versions.one)

        # Multi
        if current.spec.versions.multi != previous.spec.versions.multi:
            if current.spec.versions.multi is None:
                # remove all
                for version in previous.spec.versions.multi:
                    plan.removed.append(version)
            elif previous.spec.versions.multi is None:
                # add all
                for version in current.spec.versions.multi:
                    plan.added.append(version)
            else:
                # determine remove/add/change in the list

                # List to dict with primary key app_version
                previous_multi_dict = {i.app_version: i for i in previous.spec.versions.multi}
                current_multi_dict = {i.app_version: i for i in current.spec.versions.multi}

                # Create sets of keys only
                previous_multi_keys = set(previous_multi_dict)
                current_multi_keys = set(current_multi_dict)

                removed = list(
                    map(
                        lambda x: previous_multi_dict[x],
                        list(previous_multi_keys - current_multi_keys)
                    )
                )
                added = list(
                    map(
                        lambda x: current_multi_dict[x],
                        list(current_multi_keys - previous_multi_keys)
                    )
                )

                changed = []
                for key in list(current_multi_keys & previous_multi_keys):
                    if forced_change or current_multi_dict[key] != previous_multi_dict[key]:
                        changed.append(current_multi_dict[key])

                plan.removed = removed
                plan.added = added
                plan.changed = changed
        elif current.spec.versions.multi is not None and forced_change:
            # forced change due to package definition
            for version in current.spec.versions.multi:
                plan.changed.append(version)

        # Canary
        previous_canary_versions = []
        if previous.spec.versions.multi is not None:
            for version in previous.spec.versions.multi:
                if version.weight is not None:
                    previous_canary_versions.append(version)

        current_canary_versions = []
        if current.spec.versions.multi is not None:
            for version in current.spec.versions.multi:
                if version.weight is not None:
                    current_canary_versions.append(version)

        len_previous_canary_versions = len(previous_canary_versions)
        len_current_canary_versions = len(current_canary_versions)

        if len_previous_canary_versions > 0: # was used
            if len_current_canary_versions > 0: # still used
                if forced_change or previous_canary_versions != current_canary_versions:
                    plan.canary_versions = current_canary_versions
            else: # not used anymore
                plan.removed_canary = True
        elif len_current_canary_versions > 0: # will be used
            plan.canary_versions = current_canary_versions

        return plan

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

        if spec.white_label is not None:
            keybase = settings.DEFAULT_PKG_HELM_DEFINITIONS["keys"]["white-label"]
            args.extend(
                [
                    "--set",
                    keybase + ".enabled=true",
                    "--set",
                    f"{keybase}.rebrand={spec.white_label.rebrand}",
                    "--set",
                    f"{keybase}.marketer={spec.white_label.marketer}",
                ]
            )

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

    def _reconciliation_uninstall(self, namespace: str, release: str):
        """
        Run uninstall
        """
        self.uninstall(
            namespace,
            label_rfc1035(release)
        )
