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
import threading
import tarfile
from enum import IntEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Union, Optional, Tuple
from ..typing.targets import TargetsEnum
from ..typing.profiles import ProfileEnum
from ..typing.charts import ChartKind
from ..typing.projects import ProjectKind, InstallSpec, ProjectReconciliationPlan
from ..typing.versions import OneSpec, MultiSpec
from ..utils.external import execute, get_stdout
from ..utils.io import read_yaml, write_yaml
from ..utils.transformation import label_rfc1035
from ..targets import Targets
from ..profiles import Profiles
from ..package.helm import Helm
from ..package.svcat import ServiceCatalog
from ..errors import ChartNotFound, KustomizeStructure
from .. import settings

class HelmRepoUpdate(IntEnum):
    """Helm repositories updated or not"""
    NOT_UPDATED=0
    UPDATED=1

class HelmInstall():
    """
    Manages Helm upgrade/install and everything around that process
    """
    LOCK = threading.Lock()

    def __init__(self, dry_run: bool, kube_context: str = None):
        self._dry_run = dry_run
        self._kube_context = kube_context

    @property
    def dry_run(self) -> bool:
        """Are we in dry-run mode ?"""
        return self._dry_run

    def global_flags(self) -> List[str]:
        """
        Global flags for Helm

        --kube-context
        """
        if self._kube_context is None:
            return []

        return [
            "--kube-context",
            self._kube_context
        ]

    @classmethod
    def update(cls):
        """
        Update repositories

        helm repo update
        """

        # protect helm repo update to avoid conflict (shared setup)
        with HelmInstall.LOCK:
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

        # trying to get the chart without running repo update first
        # if we are not able to find it, we will try again after an update !
        for state in (HelmRepoUpdate.NOT_UPDATED, HelmRepoUpdate.UPDATED):
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
                if state == HelmRepoUpdate.NOT_UPDATED:
                    cls.update()
                else:
                    raise ChartNotFound(keyword)
            else:
                break # we got one

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

    @classmethod
    def untar(cls, pkg: Path, dst: Path) -> Path:
        """
        untar the local package
        """
        logging.debug("untar local package %s", os.fspath(pkg))

        with tarfile.open(pkg, "r:gz") as tar:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, dst)

        return list(dst.glob("*"))[0]

    def upgrade(self, namespace: str, release: str, chart: Union[str,Path], env: str, # pylint: disable=too-many-arguments,too-many-locals
        pre_processing_path: Path, profiles: List[ProfileEnum], cargs: List[str],
        extra_envs: dict = None, target: TargetsEnum = None):
        """
        helm upgrade {release} {chart} ...
        """

        # Get the chart
        pkg = self.search_latest(chart) if isinstance(chart, str) else None

        logging.info(
            "Installation of %s in namespace %s (chart: %s)",
            release, namespace,
            f'{pkg["name"]}-{pkg["version"]}' if pkg is not None else chart.name
        )

        with TemporaryDirectory(prefix=settings.TMP_PREFIX) as tmp:
            if pkg is not None:
                # Pull it
                dst = self.pull(pkg, Path(tmp))
            else:
                # Untar local package
                dst = self.untar(chart, Path(tmp))

            # noops.yaml (chart kind)
            chartkind = self._chart_kind(dst)

            # Values
            values_args = Helm.helm_values_args(env, dst)
            values_args += Targets.helm_targets_args(
                chartkind.spec.package.supported.target_classes, target, env, dst)

            # kustomize
            kustomize_helm_args, pp_kustomize_args = self._kustomize(dst, env)

            # Service Catalog - template file
            _svcat_template = ServiceCatalog.get_svcat_template_path(dst)
            pp_svcat_args = ["-t", os.fspath(_svcat_template)] if _svcat_template.exists() else []

            # pre-processing
            # args to pass: -e env -c chart_dir -f values1.yaml -f valuesN.yaml -t tpl1.yaml ...
            for pre_processing in chartkind.spec.package.helm.preprocessing:
                _ = execute(
                    os.fspath(pre_processing_path / pre_processing),
                    [ "-e", env, "-c", os.fspath(dst) ] + \
                        values_args + pp_svcat_args + pp_kustomize_args,
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
                ] + self.global_flags() + values_args + kustomize_helm_args + cargs,
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
            ] + self.global_flags(),
            dry_run=self.dry_run,
            capture_output=True
        )

    @classmethod
    def _chart_kind(cls, dst: Path) -> ChartKind: # pragma: no cover
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
    def _reorder(cls, values: List, ordered: List) -> List:
        """
        Reorder a list of values based on an ordered list

        list of values was previously a set that can change order.
        We need to reorder those values that are an unorderd subset of ordered list

        IMPORTANT: values is altered by sort
        """
        # TODO: Improve algorithm (not efficient)
        values.sort(key=lambda value: ordered.index(value)) # pylint: disable=unnecessary-lambda
        return values

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

                # Create list of keys only (ordered)
                previous_multi_keys_ordered = list(previous_multi_dict)
                current_multi_keys_ordered = list(current_multi_dict)

                removed = list(
                    map(
                        lambda x: previous_multi_dict[x],
                        # list(previous_multi_keys - current_multi_keys)
                        cls._reorder(
                            list(previous_multi_keys - current_multi_keys),
                            previous_multi_keys_ordered)
                    )
                )
                added = list(
                    map(
                        lambda x: current_multi_dict[x],
                        # list(current_multi_keys - previous_multi_keys)
                        cls._reorder(
                            list(current_multi_keys - previous_multi_keys),
                            current_multi_keys_ordered)
                    )
                )

                changed = []
                for key in cls._reorder(
                    list(current_multi_keys & previous_multi_keys),
                    current_multi_keys_ordered):

                    if forced_change or current_multi_dict[key] != previous_multi_dict[key]:
                        changed.append(current_multi_dict[key])

                plan.removed.extend(removed)
                plan.added.extend(added)
                plan.changed.extend(changed)
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

    @classmethod
    def _kustomize(cls, dst: Path, env: str) -> Tuple[List,List]:
        kustomize = dst / "kustomize"
        kustomize_base = kustomize / "base"
        kustomize_env = kustomize / env

        if not kustomize_env.exists():
            kustomize_env = None
        if not kustomize_base.exists():
            kustomize_base = None

        if not kustomize_env and not kustomize_base:
            return [],[]
        if kustomize_env and not kustomize_base:
            raise KustomizeStructure()

        # Helm post-renderer can't use arguments so we need to store kustomize path prior
        # This file will be read by noopshpr to run kustomize in it
        hpr = Path(settings.DEFAULT_WORKDIR) / settings.DEFAULT_NOOPS_HPR
        hpr_content = {
            "base": kustomize_base,
            "kustomize": kustomize_env or kustomize_base
        }
        write_yaml(hpr, hpr_content)

        post_renderer = [
            "--post-renderer",
            "noopshpr"
        ]

        if kustomize_env is not None:
            return post_renderer, [
                "-k", os.fspath(kustomize_base),
                "-k", os.fspath(kustomize_env)
            ]

        return post_renderer, [
            "-k", os.fspath(kustomize_base)
        ]
