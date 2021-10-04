"""
NoOps

Core component

- noops config merger
- Caching
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
import errno
import json
import tempfile
import shutil
import stat
from typing import Union
import yaml
from . import settings
from .utils.external import execute
from .utils import containers
from .utils import io

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

        # NoOps Merged configuration
        self.noops_config = containers.merge(noops_devops, noops_product)
        logging.debug("Merged config: %s", self.noops_config)

        # NoOps final configuration
        selectors=[
            "package.docker.dockerfile",
            "package.lib.dockerfile",
            "package.helm.chart",
            "package.helm.preprocessor",
            "local.build.posix",
            "local.build.nt",
            "local.run.posix",
            "local.run.nt",
        ]

        for selector in selectors:
            self._file_selector(product_path, selector, noops_product, noops_devops)

        for target, cfg in self.noops_config["pipeline"].items():
            for key in cfg.keys():
                self._file_selector(product_path, f"pipeline.{target}.{key}",
                    noops_product, noops_devops)

        self.noops_config["package"]["helm"]["values"] = \
            self.noops_config["package"]["helm"]["chart"] / "noops"

        io.write_json(
            self._get_generated_noops_json(),
            self.noops_config
        )
        io.write_yaml(
            self._get_generated_noops_yaml(),
            self.noops_config
        )

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
        noops_product: dict, noops_devops: dict):
        """
        Determines the file to use between product and devops directories

        Product (noops_product) has the highest priority over devops (noops_devops).

        Product can refer to a file located in product or devops directory.
        Devops can ONLY refer to a file located in devops directory.

        File exists in both directories (same path for each directory):
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

        product_iter = noops_product
        devops_iter = noops_devops
        config_iter = self.noops_config

        for key in keys[:-1]:
            product_iter = product_iter.get(key, {})
            devops_iter = devops_iter.get(key, {})

            # create config entry if missing
            # product and devops can set different subset of keys
            if config_iter.get(key) is None:
                config_iter[key]={}
            config_iter = config_iter[key]

        # value in product and devops config
        product_file = product_iter.get(keys[-1])
        devops_file = devops_iter.get(keys[-1])

        # Order is important.
        # Product definition has highest priority over devops definition
        if product_file is not None:
            # check if the file is in product or devops
            # priority to product directory
            if (product_path / product_file).exists():
                # product directory
                product_file_path = product_path / product_file
            elif (self.workdir /product_file).exists():
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

        if devops_file is not None:
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
            print(json.dumps(self.noops_config, indent=indent))
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
