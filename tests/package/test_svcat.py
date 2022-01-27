"""
Tests noops.package.svcat
"""

import os
from pathlib import Path
from noops.noops import NoOps
from noops.package.svcat import ServiceCatalog
from noops.package.helm import Helm
from ..test_noops import product_copy, read_yaml_base, read_yaml
from .. import TestCaseNoOps

SVCAT=Path("tests/data/package/svcat/product").resolve()
PROCESSING=Path("tests/data/package/svcat/processing").resolve()

class Test(TestCaseNoOps):
    """
    Tests noops.package.svcat
    """

    def test_noops_with_svcat(self):
        """NoOps with Service Catalog"""

        with product_copy(SVCAT) as product_path:
            _ = os.environ.pop("NOOPS_SVCAT_PROCESSING")
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            expected = read_yaml_base(SVCAT / "tests/noops-generated.yaml", product_path)

            # memory test
            self.assertEqual(
                noops.noops_config,
                expected
            )

    def test_svcat_init(self):
        """Init Service Catalog without processing"""
        with product_copy(SVCAT) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            svcat = ServiceCatalog(noops, "FAKE_HELM")

            self.assertEqual(
                svcat.helm,
                "FAKE_HELM"
            )

            self.assertIs(
                svcat.core,
                noops
            )

            self.assertIsNone(svcat._processing) # pylint: disable=protected-access

    def test_svcat_init_processing(self):
        """Init Service Catalog with processing"""
        with product_copy(SVCAT) as product_path:
            os.environ["NOOPS_SVCAT_PROCESSING"] = os.fspath(PROCESSING)

            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            svcat = ServiceCatalog(noops, "FAKE_HELM")

            self.assertEqual(
                svcat._processing, # pylint: disable=protected-access
                PROCESSING
            )

    def test_internal_converter(self):
        """OpenBroker Service Catalog"""

        with product_copy(SVCAT) as product_path:
            content = read_yaml(product_path / "noops.yaml")

            service_request = content["service-catalog"][0]
            name = "myservice"

            result = ServiceCatalog._internal_converter( # pylint: disable=protected-access
                name, service_request
            )

            self.assertEqual(
                result,
                [
                    {
                        'apiVersion': 'servicecatalog.k8s.io/v1beta1',
                        'kind': 'ServiceInstance',
                        'spec': {
                            'clusterServiceClassExternalName': 'broker_class',
                            'clusterServicePlanExternalName': 'broker_plan',
                            'parameters': {
                                'key': 'instance'
                            }
                        }
                    },
                    {
                        'apiVersion': 'servicecatalog.k8s.io/v1beta1',
                        'kind': 'ServiceBinding',
                        'spec': {
                            'instanceRef': {
                                'name': 'myservice'
                            },
                            'parameters': {
                                'key': 'binding'
                            }
                        }
                    }
                ]
            )

    def test_external_converter(self):
        """Operator or anything else"""

        with product_copy(SVCAT) as product_path:
            content = read_yaml(product_path / "noops.yaml")

            service_request = content["service-catalog"][1]
            name = "myservice"

            result = ServiceCatalog._external_converter( # pylint: disable=protected-access
                name, service_request, PROCESSING / "operator/plan"
            )

            self.assertEqual(
                result,
                [
                    {
                        'apiVersion': 'unittest.local/v1',
                        'kind': 'Test',
                        'spec': {'key': 'value'}
                    }
                ]
            )

    def test_kinds_and_values(self):
        """Create Kinds and values"""

        with product_copy(SVCAT) as product_path:
            os.environ["NOOPS_SVCAT_PROCESSING"] = os.fspath(PROCESSING)

            noops = NoOps(product_path, dry_run=False, rm_cache=True)
            helm = Helm(noops)

            ServiceCatalog(noops, helm).create_kinds_and_values()

            svcat_templates = noops.workdir / "helm/chart/templates/svcat.yaml"

            self.assertEqual(
                svcat_templates.read_text(encoding="UTF-8"),
                """apiVersion: servicecatalog.k8s.io/v1beta1
kind: ServiceInstance
metadata:
  annotations: {{ include "demo.annotations" . | nindent 4 }}
  labels: {{ include "demo.labels" . | nindent 4 }}
  name: svc1-binding
spec:
  clusterServiceClassExternalName: broker_class
  clusterServicePlanExternalName: broker_plan
  parameters:
    key: instance
---
apiVersion: servicecatalog.k8s.io/v1beta1
kind: ServiceBinding
metadata:
  annotations: {{ include "demo.annotations" . | nindent 4 }}
  labels: {{ include "demo.labels" . | nindent 4 }}
  name: svc1-binding
spec:
  instanceRef:
    name: svc1-binding
  parameters:
    key: binding
---
apiVersion: unittest.local/v1
kind: Test
metadata:
  annotations: {{ include "demo.annotations" . | nindent 4 }}
  labels: {{ include "demo.labels" . | nindent 4 }}
  name: svc2-binding
spec:
  key: value
---
"""
            )

            svcat_binding = noops.workdir / "helm/chart/noops/values-svcat.yaml"

            self.assertEqual(
                svcat_binding.read_text(encoding="UTF-8"),
                """svcat:\n  bindings:\n  - svc1-binding\n  - svc2-binding\n"""
            )
