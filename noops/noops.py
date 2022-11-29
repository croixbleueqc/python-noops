"""
NoOps

Core component

- noops config merger
- Caching
"""

# Copyright 2021-2022 Croix Bleue du Québec

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
import errno
import json
import tempfile
import shutil
import stat
from typing import Union
import yaml
import jsonschema
from . import settings
from .utils.external import execute
from .utils import containers, io, resources

class NoOps():
    """
    NoOps Core
    """

    def __init__(
        self, product_path: Union[str, Path], dry_run: bool, rm_cache: bool):

        logging.info("NoOps: Init...")

        # Use absolute path
        product_path = Path(product_path).resolve()

        # change working directory to the product path
        os.chdir(product_path)

        self.dry_run = dry_run
        self.workdir = product_path / settings.DEFAULT_WORKDIR

        if rm_cache or not self._iscache():
            self._create_cache(product_path)
            self._jsonschema_validate(product_path)
        else:
            self._load_cache()

        logging.debug("Final config: %s", self.noops_config)

        # Done
        logging.info("NoOps: Ready !" if not dry_run else "NoOps: Dry-run mode ready !")

    def _iscache(self) -> bool:
        return self._get_generated_noops_json().is_file() and \
            self._get_generated_noops_yaml().is_file()

    def _create_cache(self, product_path: Path):
        # remove possible cache
        if self.workdir.exists():
            logging.info("purging cache")
            shutil.rmtree(self.workdir)

        logging.info("creating cache")

        # Load product noops.yaml
        noops_product = io.read_yaml(product_path / settings.DEFAULT_NOOPS_FILE)
        logging.debug("Product config: %s", noops_product)

        # Load devops noops.yaml
        self._prepare_devops(noops_product.get("devops", {}))

        noops_devops = io.read_yaml(self.workdir / settings.DEFAULT_NOOPS_FILE)
        logging.debug("DevOps config: %s", noops_devops)

        # Merge product and devops (product override devops)
        noops_merged = containers.merge(noops_devops, noops_product)
        logging.debug("Merged config: %s", noops_merged)

        # NoOps Profile Merged configuration (profile orverride)
        profile = noops_merged.get("profile")
        if profile:
            self.noops_config = containers.merge(noops_merged, noops_merged["profiles"][profile])
        else:
            self.noops_config = noops_merged
        logging.debug("%s profile merged config: %s", profile, self.noops_config)

        # Check and set files path to used
        selectors=[
            "package.docker.dockerfile",
            "package.lib.dockerfile",
            "package.helm.chart",
            "package.helm.chart.destination",
            "package.helm.preprocessor",
            "package.helm.kustomize",
            "local.build.posix",
            "local.build.nt",
            "local.run.posix",
            "local.run.nt"
        ]

        if profile:
            noops_product_profile = noops_product.get("profiles", {}).get(profile, {})
            noops_devops_profile = noops_devops.get("profiles", {}).get(profile, {})
        else:
            noops_product_profile = {}
            noops_devops_profile = {}

        for selector in selectors:
            self._file_selector(product_path, selector,
                                noops_product, noops_devops,
                                noops_product_profile, noops_devops_profile)

        # pipeline.<target>.{ci,cd,pr,default,*}
        for target, cfg in self.noops_config["pipeline"].items():
            for key in cfg.keys():
                self._file_selector(product_path, f"pipeline.{target}.{key}",
                    noops_product, noops_devops,
                    noops_product_profile, noops_devops_profile)

        # package.docker.<target>.{dockerfile}
        for target, cfg in self.noops_config["package"]["docker"].items():
            if isinstance(cfg, dict) and "dockerfile" in cfg.keys():
                self._file_selector(product_path, f"package.docker.{target}.dockerfile",
                    noops_product, noops_devops,
                    noops_product_profile, noops_devops_profile)

        chart = self.noops_config["package"]["helm"]["chart"]

        # Set computed package.helm.values
        if isinstance(chart, dict):
            self.noops_config["package"]["helm"]["values"] = \
                chart["destination"] / "noops"
        elif chart is not None:
            self.noops_config["package"]["helm"]["values"] = \
                chart / "noops"

        # Pull helm/chart (if necessary)
        if isinstance(chart, dict):
            self._pull_helm_chart(chart)

        # Deprecated
        self._deprecated_noops()

        # NoOps final configuration
        io.write_json(
            self._get_generated_noops_json(),
            self.noops_config
        )
        io.write_yaml(
            self._get_generated_noops_yaml(),
            self.noops_config
        )

    def _jsonschema_validate(self, product_path: Path):
        logging.info("validating generated configuration")

        # Order is important (first one available is used)
        schema_paths = [
            product_path / settings.SCHEMA_FILE, # product schema
            self.workdir / settings.SCHEMA_FILE  # devops schema
        ]

        instance = io.read_json(self._get_generated_noops_json())

        def _validate(schema_path: Path):
            schema_defs = io.read_yaml(schema_path)
            jsonschema.validate(instance=instance, schema=schema_defs)

        for schema_path in schema_paths:
            if schema_path.exists():
                _validate(schema_path)
                return

        # built-in fallback
        with resources.schema_path_ctx() as schema_path:
            _validate(schema_path)

    def _deprecated_noops(self):
        warn_path=[
            ("package.docker.dockerfile", "package.docker.<target>.dockerfile"),
            ("package.lib.dockerfile", "package.docker.lib.dockerfile"),
            ("package.helm.preprocessor", "package.helm.pre-processing")
        ]

        for deprecated_path, new_path in warn_path:
            keys = deprecated_path.split(".")
            cfg = self.noops_config

            try:
                for key in keys:
                    cfg = cfg[key]
            except KeyError:
                cfg = None

            if cfg is not None:
                logging.warning("%s is DEPRECATED! Please use %s", deprecated_path, new_path)

    def _pull_helm_chart(self, chart: dict):
        logging.info("pulling helm chart")

        url = chart.get("url")
        name = chart.get("name")
        version = chart.get("version")
        dst = chart.get("destination")

        with tempfile.TemporaryDirectory(prefix="noops-") as tmpdirname:
            args = [
                "pull",
                name or url, # if both are set, name is prefered
                "--untar", "--untardir", tmpdirname
            ]
            if name and version is not None:
                args.append("--version")
                args.append(version)

            _ = execute(
                "helm",
                args,
                capture_output=True,
                dry_run=self.is_dry_run()
            )

            # Move chart in final destination
            if self.is_dry_run():
                return

            tmp = Path(tmpdirname)
            chart = list(tmp.glob("*"))[0]
            shutil.rmtree(dst)
            shutil.move(chart, dst)

    def _load_cache(self):
        logging.info("loading cached configuration")

        self.noops_config = io.read_yaml(self._get_generated_noops_yaml())

    def _get_generated_noops_json(self) -> Path:
        return self.workdir / f"{settings.GENERATED_NOOPS}.json"

    def _get_generated_noops_yaml(self) -> Path:
        return self.workdir / f"{settings.GENERATED_NOOPS}.yaml"

    def _prepare_devops(self, devops_config: dict):
        """
        Prepare the workdir folder by copying a devops structure
        from a local tree or from a git repository.
        """
        local_config = devops_config.get("local")
        git_config = devops_config.get("git")

        if local_config:
            shutil.copytree(
                local_config["path"],
                self.workdir
            )
            return

        if git_config:
            with tempfile.TemporaryDirectory(prefix="noops-") as tmpdirname:
                clone_path = Path(tmpdirname) / settings.DEFAULT_WORKDIR

                # clone
                execute(
                    "git",
                    [
                        "clone",
                        "--depth=1",
                        "--branch={}".format(git_config["branch"]), # pylint: disable=consider-using-f-string
                        git_config["clone"],
                        os.fspath(clone_path)
                    ]
                )

                # remove .git folder
                shutil_kwargs={}
                if os.name == "nt":
                    def remove_readonly(callback, path, excinfo): # pylint: disable=unused-argument
                        # Some files in .git folder are flagged read only on Windows
                        Path(path).chmod(stat.S_IWRITE)
                        callback(path)
                    shutil_kwargs["onerror"]=remove_readonly

                shutil.rmtree(clone_path / ".git", **shutil_kwargs)

                # move in the product folder
                shutil.move(
                    clone_path,
                    self.workdir
                )

                return

        logging.error("devops/local or devops/git not found !")
        raise ValueError()

    def _file_selector(self, product_path: Path, selector: str,
        product: dict, devops: dict,
        product_profile: dict, devops_profile: dict):
        """
        Determines the file to use between product and devops directories

        Product has the highest priority over DevOps.
        Product profile has the highest priority over DevOps profile.
        Profile has the highest priority over all.

        Product can refer to a file located in product or devops directory.
        Devops can ONLY refer to a file located in devops directory.

        If a file exists in Product and DevOps (same relative path for each):
        - if product refer it, the file in product directory will be used.
        - if devops is the ONLY one to refer it, the devops file will be used.

        eg:
            From DevOps:
              devops/Dockerfile
              devops/Dockerfile.distroless

            From Product:
              package.docker.Dockerfile can be set to devops/Dockerfile{.distroless}

        If a requested file does NOT exist, a FileNotFoundError exception will be raised.
        """
        logging.debug("file selector for '%s'", selector)

        keys = selector.split(".")

        product_iter = product
        devops_iter = devops
        product_profile_iter = product_profile
        devops_profile_iter = devops_profile
        config_iter = self.noops_config

        for key in keys[:-1]:
            product_iter = product_iter.get(key, {})
            devops_iter = devops_iter.get(key, {})
            product_profile_iter = product_profile_iter.get(key, {})
            devops_profile_iter = devops_profile_iter.get(key, {})

            config_iter = config_iter.get(key)
            if config_iter is None:
                # the selector is not used in the final configuration. skip it now !
                return

        # Determine the product and/or devops file to use
        product_file = product_iter.get(keys[-1]) if isinstance(product_iter, dict) else None
        devops_file = devops_iter.get(keys[-1]) if isinstance(devops_iter, dict) else None
        product_profile_file = product_profile_iter.get(keys[-1]) \
            if isinstance(product_profile_iter, dict) else None
        devops_profile_file = devops_profile_iter.get(keys[-1]) \
            if isinstance(devops_profile_iter, dict) else None

        if devops_profile_file is not None:
            # DevOps profile has a higher priority over product_file/devops_file
            product_file = None
            devops_file = devops_profile_file

        if product_profile_file is not None:
            # Product profile has the highest priority
            product_file = product_profile_file

        # Order is important.
        # Product definition has highest priority over devops definition
        if isinstance(product_file, str):
            # check if the file is in product or devops
            # priority to product directory
            if (product_path / product_file).exists():
                # product directory
                product_file_path = product_path / product_file
            elif (self.workdir / product_file).exists():
                # devops (workdir) directory
                product_file_path = self.workdir / product_file
            else:
                raise FileNotFoundError(
                    errno.ENOENT,
                    os.strerror(errno.ENOENT),
                    product_file
                )

            config_iter[keys[-1]] = product_file_path
            return

        if isinstance(devops_file, str):
            devops_file_path = self.workdir / devops_file
            if devops_file_path.exists():
                config_iter[keys[-1]] = devops_file_path
            else:
                raise FileNotFoundError(
                    errno.ENOENT,
                    os.strerror(errno.ENOENT),
                    devops_file
                )
            return

        logging.debug("key '%s' is not set ! [skip]", selector)

    def output(self, asjson=False, indent=settings.DEFAULT_INDENT):
        """
        Print the final noops configuration in a json or yaml way
        """
        if asjson:
            print(json.dumps(self.noops_config, indent=indent, cls=io.PathEncoder))
        else:
            print(yaml.dump(self.noops_config, indent=indent))

    def is_dry_run(self) -> bool:
        """
        Are we in dry-run mode ?
        """
        return self.dry_run

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a specific feature is enabled
        """
        try:
            return self.noops_config["features"][feature]
        except KeyError:
            return settings.DEFAULT_FEATURES[feature]

    def noops_envs(self):
        """
        Environment variables to expose when we need to execute a command
        """
        return {
            "NOOPS_GENERATED_JSON": self._get_generated_noops_json(),
            "NOOPS_GENERATED_YAML": self._get_generated_noops_yaml()
        }
