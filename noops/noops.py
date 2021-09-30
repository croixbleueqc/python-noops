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
import json
import tempfile
import shutil
import stat
import yaml
from . import helper
from .package.helm import Helm
from .svcat import ServiceCatalog
from .utils.external import execute

class NoOps():
    """
    NoOps Core
    """

    def __init__(
        self, product_path: str, dry_run: bool, rm_cache: bool):

        logging.info("NoOps: Init...")

        # Use absolute path
        product_path = os.path.abspath(product_path)

        # change working directory to the product path
        os.chdir(product_path)

        self.dry_run = dry_run
        self.workdir = os.path.join(product_path, helper.DEFAULT_WORKDIR)

        if rm_cache or not self._iscache():
            self._create_cache(product_path)

        self._load_cache()

        logging.debug("Final config: %s", self.noops_config)

        # Done
        logging.info("NoOps: Ready !" if not dry_run else "NoOps: Dry-run mode ready !")

    def _iscache(self) -> bool:
        return os.path.isfile(self._get_generated_noops_json()) and \
            os.path.isfile(self._get_generated_noops_yaml())

    def _create_cache(self, product_path: str):
        # remove possible cache
        if os.path.exists(self.workdir):
            logging.info("purging cache")
            shutil.rmtree(self.workdir)

        logging.info("creating cache")

        # Load product noops.yaml
        noops_product = helper.read_yaml(
            os.path.join(product_path, helper.DEFAULT_NOOPS_FILE)
            )
        logging.debug("Product config: %s", noops_product)

        # Load devops noops.yaml
        self._prepare_devops(noops_product.get("devops", {}))

        noops_devops = helper.read_yaml(
            os.path.join(self.workdir, helper.DEFAULT_NOOPS_FILE)
            )
        logging.debug("DevOps config: %s", noops_devops)

        # NoOps Merged configuration
        self.noops_config = helper.merge(noops_devops, noops_product)
        logging.debug("Merged config: %s", self.noops_config)

        # NoOps final configuration
        selectors=[
            "package.docker.dockerfile",
            "package.lib.dockerfile",
            "package.helm.chart",
            "package.helm.preprocessor",
            "pipeline.deploy.default",
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

        self.noops_config["package"]["helm"]["values"] = os.path.join(
            self.noops_config["package"]["helm"]["chart"], "noops"
        )

        helper.write_json(
            self._get_generated_noops_json(),
            self.noops_config
        )
        helper.write_yaml(
            self._get_generated_noops_yaml(),
            self.noops_config
        )

    def _load_cache(self):
        logging.info("loading cached configuration")

        self.noops_config = helper.read_yaml(self._get_generated_noops_yaml())

    def _get_generated_noops_json(self):
        return os.path.join(self.workdir, f"{helper.GENERATED_NOOPS}.json")

    def _get_generated_noops_yaml(self):
        return os.path.join(self.workdir, f"{helper.GENERATED_NOOPS}.yaml")

    def helm(self, chart_name: str = None) -> Helm:
        """
        New Helm instance
        """
        return Helm(self, chart_name)

    def service_catalog(self) -> ServiceCatalog:
        """
        New Service Catalog instance
        """
        return ServiceCatalog(self)

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
                clone_path = os.path.join(tmpdirname, helper.DEFAULT_WORKDIR)

                # clone
                execute(
                    "git",
                    [
                        "clone",
                        "--depth=1",
                        "--branch={}".format(git_config["branch"]), # pylint: disable=consider-using-f-string
                        git_config["clone"],
                        clone_path
                    ]
                )

                # remove .git folder
                shutil_kwargs={}
                if os.name == "nt":
                    def remove_readonly(callback, path, excinfo): # pylint: disable=unused-argument
                        # Some files in .git folder are flagged read only on Windows
                        os.chmod(path, stat.S_IWRITE)
                        callback(path)
                    shutil_kwargs["onerror"]=remove_readonly

                shutil.rmtree(os.path.join(clone_path, ".git"), **shutil_kwargs)

                # move in the product folder
                shutil.move(
                    clone_path,
                    self.workdir
                )

                return

        logging.error("devops/local or devops/git not found !")
        raise ValueError()

    def _file_selector(self, product_path: str, selector: str,
        noops_product: dict, noops_devops: dict):
        """
        Determines the file to use (remote vs local)

        The main target is to use a devops file (remote)
        This one can be overriden with another version located with the product (local)
        """
        logging.debug("file selector for: %s", selector)

        keys = selector.split(".")

        product_iter = noops_product
        devops_iter = noops_devops
        config_iter = self.noops_config

        for key in keys[:-1]:
            product_iter = product_iter.get(key, {})
            devops_iter = devops_iter.get(key, {})

            if config_iter.get(key) is None:
                config_iter[key]={}
            config_iter = config_iter[key]

        product_file = product_iter.get(keys[-1])
        devops_file = devops_iter.get(keys[-1])

        if product_file is None:
            if devops_file is not None:
                config_iter[keys[-1]] = os.path.join(self.workdir, devops_file)
            else:
                logging.debug("selector %s is not set", selector)
        else:
            config_iter[keys[-1]] = os.path.join(product_path, product_file)

    def output(self, asjson=False, indent=helper.DEFAULT_INDENT):
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
            return helper.DEFAULT_FEATURES[feature]

    def prepare(self):
        """
        Generates everything that is needed by the product and set with the noops.yaml

        - Service Catalog
        - Helm values
        """

        # Service Catalog
        if self.is_feature_enabled("service-catalog"):
            self.service_catalog().create_kinds_and_values()
        else:
            logging.info("Service Catalog feature disabled")

        # Helm values-*.yaml
        self.helm().create_values()

    def noops_envs(self):
        """
        Environment variables to expose when we need to execute a command
        """
        return {
            "NOOPS_GENERATED_JSON": self._get_generated_noops_json(),
            "NOOPS_GENERATED_YAML": self._get_generated_noops_yaml()
        }
