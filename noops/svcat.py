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

import logging
import yaml
import os
from . import helper

class ServiceCatalog(object):
    SERVICE_CATALOG="service-catalog"

    def __init__(self, core):
        self.core = core

    def create_kinds_and_values(self):
        """
        Create:
        - kinds ServiceInstance/ServiceBinding in {package.helm.chart}/templates/svcat.yaml
        - bindings available in {workdir}/helm/values-svcat.yaml
        """
        svcat_bindings=[]
        svcat_kinds = ""

        logging.info("Creating service catalog kinds...")

        for svcat in self.core.noops_config.get(ServiceCatalog.SERVICE_CATALOG, []):
            logging.info(f" ... {svcat['name']}")

            instance_name="{}-instance".format(svcat["name"])
            binding_name="{}-binding".format(svcat["name"])

            instance = {
                "apiVersion": "servicecatalog.k8s.io/v1beta1",
                "kind": "ServiceInstance",
                "metadata": {
                    "name": instance_name,
                    "labels": self.core.helm.include("labels", 4),
                    "annotations": self.core.helm.include("annotations", 4)
                },
                "spec": {
                    "clusterServiceClassExternalName": svcat["class"],
                    "clusterServicePlanExternalName": svcat["plan"],
                    "parameters": svcat["instance"]["parameters"]
                }
            }

            binding = {
                "apiVersion": "servicecatalog.k8s.io/v1beta1",
                "kind": "ServiceBinding",
                "metadata": {
                    "name": binding_name,
                    "labels": self.core.helm.include("labels", 4),
                    "annotations": self.core.helm.include("annotations", 4)
                },
                "spec": {
                    "instanceRef": {
                        "name": instance["metadata"]["name"]
                    },
                    "parameters": svcat["binding"]["parameters"]
                }
            }

            # append to svcat kinds definitions
            svcat_kinds += self.core.helm.as_chart_template(yaml.dump(instance, indent=helper.DEFAULT_INDENT))
            svcat_kinds += "---\n"
            svcat_kinds += self.core.helm.as_chart_template(yaml.dump(binding, indent=helper.DEFAULT_INDENT))
            svcat_kinds += "---\n"

            # add to global bindings array
            svcat_bindings.append(binding_name)
        
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

