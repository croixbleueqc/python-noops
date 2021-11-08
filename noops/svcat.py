"""
Service Catalog

Handles "service-catalog" section of noops.yaml

Convert to a kind objects injected in an helm chart
Expose bindings to use in a values-svcat.yaml file
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

from typing import Optional, List
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import logging
import yaml
import os
from . import helper

class ServiceCatalog(object):
    SERVICE_CATALOG="service-catalog"

    def __init__(self, core):
        self.core = core

        processing = os.environ.get("NOOPS_SVCAT_PROCESSING")
        if processing is not None:
            self._processing = Path(processing)
        else:
            self._processing = None

    @classmethod
    def _external_converter(cls, name:str, service_request: dict, converter: Path) -> List[dict]:
        """
        Use an external converter to create Service Catalog objects
        """
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            request = tmp / "request.yaml"
            objects = tmp / "objects.yaml"

            with request.open("w", encoding="UTF-8") as stream:
                yaml.dump(service_request, stream)

            subprocess.run(
                [
                    os.fspath(converter),
                    "-n", name,
                    "-r", os.fspath(request),
                    "-o", os.fspath(objects)
                ],
                shell=False,
                check=True
            )

            return yaml.safe_load(objects.read_text(encoding='UTF-8'))

    @classmethod
    def _internal_converter(cls, name: str, service_request: dict) -> List[dict]:
        """
        Assume that this is a standard Service Catalog
        """

        instance = {
            "apiVersion": "servicecatalog.k8s.io/v1beta1",
            "kind": "ServiceInstance",
            "spec": {
                "clusterServiceClassExternalName": service_request["class"],
                "clusterServicePlanExternalName": service_request["plan"],
                "parameters": service_request["instance"]["parameters"]
            }
        }

        binding = {
            "apiVersion": "servicecatalog.k8s.io/v1beta1",
            "kind": "ServiceBinding",
            "spec": {
                "instanceRef": {
                    "name": name
                },
                "parameters": service_request["binding"]["parameters"]
            }
        }

        return [instance, binding]

    def __set_metadata(self, name: str, objs: List[dict]):
        """
        Add metadata on all objects
        """
        for obj in objs:
            obj["metadata"] = {
                "name": name,
                "labels": self.core.helm.include("labels", 4),
                "annotations": self.core.helm.include("annotations", 4)
            }

    def create_kinds_and_values(self):
        """
        Create:
        - kinds ServiceInstance/ServiceBinding in {package.helm.chart}/templates/svcat.yaml
        - bindings available in {workdir}/helm/values-svcat.yaml
        """
        svcat_bindings=[]

        logging.info("Creating service catalog kinds...")

        svcat_objs = []
        for svcat in self.core.noops_config.get(ServiceCatalog.SERVICE_CATALOG, []):
            logging.info(f" ... {svcat['name']}")

            use_external = False
            if self._processing is not None:
                external_converter = self._processing / svcat['class'] / svcat["plan"]
                if external_converter.exists():
                    use_external = True

            name="{}-binding".format(svcat["name"])

            if use_external:
                objs = self._external_converter(name, svcat, external_converter)
            else:
                objs = self._internal_converter(name, svcat)

            # metadata
            self.__set_metadata(name, objs)

            # add to global bindings arrays
            svcat_bindings.append(name)
            svcat_objs.extend(objs)

        svcat_kinds = ""
        for obj in svcat_objs:
            # append to svcat kinds definitions
            svcat_kinds += self.core.helm.as_chart_template(yaml.dump(obj, indent=helper.DEFAULT_INDENT))
            svcat_kinds += "---\n"

        if svcat_kinds != "":
            if self.core.dryrun:
                print(svcat_kinds)
            else:
                helper.write_raw(
                    os.path.join(self.core.noops_config["package"]["helm"]["chart"], "templates", "svcat.yaml"),
                    svcat_kinds
                )

        logging.info("Creating service catalog values")

        svcat_values = {
            "svcat": {
                "bindings": svcat_bindings
            }
        }

        if self.core.dryrun:
            print(yaml.dump(svcat_values, indent=helper.DEFAULT_INDENT))
        else:
            helper.write_yaml(
                os.path.join(self.core.workdir, "helm", "values-svcat.yaml"),
                svcat_values,
                indent=helper.DEFAULT_INDENT
            )
