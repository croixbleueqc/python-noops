"""
NoOps

Core component

- noops config merger
- Caching
- expose cli functions
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

from . import helper
from .helm import Helm
from .svcat import ServiceCatalog
import logging
import os
import yaml
import json
import subprocess
import tempfile
import shutil

class NoOps(object):
    def __init__(self, product_path: str, chart_name: str, dryrun: bool, show_noops_config: bool, rm_cache: bool):
        logging.info("NoOps: Init...")

        self.dryrun = dryrun
        self.workdir = os.path.join(product_path, helper.DEFAULT_WORKDIR)
        self.product_path = product_path

        self.noops_generated_json = os.path.join(self.workdir, "noops-generated.json")
        self.noops_generated_yaml = os.path.join(self.workdir, "noops-generated.yaml")

        # Determine if we need to flush the cache or reuse it
        if rm_cache or \
            not os.path.isfile(self.noops_generated_json) or \
            not os.path.isfile(self.noops_generated_yaml):

            # flushing cache and generate final noops.yaml file

            # remove possible cache
            if os.path.exists(self.workdir):
                shutil.rmtree(self.workdir)

            logging.info("without cache")

            # Load product noops.yaml
            noops_product = helper.read_yaml(
                os.path.join(product_path, helper.DEFAULT_NOOPS_FILE)
                )
            logging.debug("Product config: {}".format(noops_product))

            # Load devops noops.yaml
            self._prepare_devops(noops_product.get("devops", {}))

            noops_devops = helper.read_yaml(
                os.path.join(self.workdir, helper.DEFAULT_NOOPS_FILE)
                )
            logging.debug("DevOps config: {}".format(noops_devops))

            # NoOps Merged configuration
            self.noops_config = helper.merge(noops_devops, noops_product)
            logging.debug("Merged config: {}".format(self.noops_config))

            # NoOps final configuration
            selectors=[
                "package.docker.dockerfile",
                "package.helm.chart",
                "package.helm.preprocessor",
                "pipeline.image.ci",
                "pipeline.image.cd",
                "pipeline.image.pr",
                "pipeline.deploy.default",
                "local.build.posix",
                "local.run.posix"
            ]

            for selector in selectors:
                self._file_selector(selector, noops_product, noops_devops)    

            self.noops_config["package"]["helm"]["values"] = os.path.join(self.workdir, "helm")

            helper.write_json(self.noops_generated_json, self.noops_config)
            helper.write_yaml(self.noops_generated_yaml, self.noops_config)
        else:
            logging.info("using cache")

            # load noops-generated.yaml from cache
            self.noops_config = helper.read_yaml(self.noops_generated_yaml)

        logging.debug("Final config: {}".format(self.noops_config))

        if show_noops_config:
            self.output()

        # Helm
        self.helm = Helm(self, chart_name)

        # Svcat
        self.svcat = ServiceCatalog(self)

        # Done
        if not dryrun:
            logging.info("NoOps: Ready !")
        else:
            logging.info("NoOps: Dry-run mode ready !")

    def _prepare_devops(self, devops_config: dict):
        """
        Prepare the workdir folder by copying a devops structure from a local tree or from a git repository.
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
                self.execute(
                    "git",
                    [
                        "clone",
                        "--depth=1",
                        "--branch={}".format(git_config["branch"]),
                        git_config["clone"],
                        clone_path
                    ],
                    forcerun=True)

                # remove .git folder
                shutil.rmtree(os.path.join(clone_path, ".git"))

                # move in the product folder
                shutil.move(
                    clone_path,
                    self.workdir
                )

                return

        logging.error("devops/local or devops/git not found !")
        raise ValueError()

    def _file_selector(self, selector: str, noops_product: dict, noops_devops: dict):
        """
        Determines the file to use (remote vs local)

        The main target is to use a devops file (remote) but this one can be overriden with another version located with the product (local)
        """
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
                logging.debug(f"selector {selector} is not set")
        else:
            config_iter[keys[-1]] = os.path.join(self.product_path, product_file)

    def output(self, asjson=False, indent=helper.DEFAULT_INDENT):
        """
        Print the final noops configuration in a json or yaml way
        """
        if asjson:
            print(json.dumps(self.noops_config, indent=indent))
        else:
            print(yaml.dump(self.noops_config, indent=indent))

    def prepare(self):
        """
        Generates everything that is needed by the product and set with the noops.yaml

        - Service Catalog
        - Helm values
        """
        # Service Catalog
        if not self.noops_config["package"].get("skip-service-catalog", False):
            self.svcat.create_kinds_and_values()
        else:
            logging.warn("skip service catalog as requested")

        # Helm values-*.yaml
        self.helm.create_values()

    def noops_envs(self):
        """
        Environment variables to expose when we need to execute a command
        """
        return {
            "NOOPS_GENERATED_JSON": self.noops_generated_json,
            "NOOPS_GENERATED_YAML": self.noops_generated_yaml
        }

    def execute(self, cmd, args, extra_envs={}, forcerun=False):
        """
        Execute a command.

        The command needs to have execution permission for the running user.
        """
        custom_envs = {**os.environ, **extra_envs}

        logging.debug("execute: {} {}".format(
            cmd,
            " ".join(args)
        ))

        if forcerun or not self.dryrun:
            subprocess.run(
                [cmd] + args,
                shell=False,
                check=True,
                env=custom_envs,
                cwd=self.product_path
            )

    def exec_common_flow(self, entries: dict, scope: str, args: dict):
        """
        Helper to execute a command with default noops environment variables and scope
        """
        extra_envs = self.noops_envs()

        self.execute(
            entries[scope],
            args,
            extra_envs
        )

    def pipeline_deploy(self, scope, custom_args):
        """
        Deploy from a pipeline
        
        scope: default
        """
        self.prepare()
        self.exec_common_flow(
            self.noops_config["pipeline"]["deploy"],
            scope,
            custom_args
        )

    def pipeline_image(self, scope, custom_args):
        """
        Build an image from a pipeline
        
        scope: ci, cd, pr
        """
        self.exec_common_flow(
            self.noops_config["pipeline"]["image"],
            scope,
            custom_args
        )

    def local_build(self, custom_args):
        """
        Build an image locally (should be a dev computer but not a pipeline)

        scope: posix, nt
        """
        self.exec_common_flow(
            self.noops_config["local"]["build"],
            os.name,
            custom_args
        )

    def local_run(self, custom_args):
        """
        Run an image locally (should be a dev computer)

        scope: posix, nt
        """
        self.exec_common_flow(
            self.noops_config["local"]["run"],
            os.name,
            custom_args
        )
