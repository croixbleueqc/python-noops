"""
Tests noops.package.helm
"""

import os
from unittest.mock import patch, call
from pathlib import Path
from noops.noops import NoOps
from noops.package.helm import Helm
from noops.package.prepare import prepare
from ..test_noops import product_copy, read_yaml_base, read_yaml
from .. import TestCaseNoOps

OVERRIDE_TAG=Path("tests/data/package/helm/override_tag.yaml").resolve()
PRODUCT=Path("tests/data/package/helm/product").resolve()

class Test(TestCaseNoOps):
    """
    Tests noops.package.helm
    """
    def test_noops_ref(self):
        """NoOps Reference Project"""

        with product_copy(PRODUCT) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            expected = read_yaml_base(PRODUCT / "tests/noops-generated.yaml", product_path)

            # memory test
            self.assertEqual(
                noops.noops_config,
                expected
            )

    def test_init_helm(self):
        """Helm init"""

        with product_copy(PRODUCT) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            helm = Helm(noops)

            self.assertIs(helm.core, noops)
            self.assertIs(helm.config, noops.noops_config["package"]["helm"])
            self.assertEqual(helm.chart_name, "demo")

            helm = Helm(noops, chart_name="test")
            self.assertEqual(helm.chart_name, "test")

    def test_templates(self):
        """Functions relative to templating"""

        with product_copy(PRODUCT) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            helm = Helm(noops)

            self.assertEqual(
                helm.include("mymacro", nindent=4, root="$"),
                '''{{ include "demo.mymacro" $ | nindent 4 }}'''
            )

            self.assertEqual(
                helm.as_chart_template(
                    '{{noops:chart:include:fullname}}\n{{noops:chart:include:other}}'
                ),
                '{{ include "demo.fullname" . }}\n{{ include "demo.other" . }}'
            )

    def test_create_values(self):
        """Create values"""

        with product_copy(PRODUCT) as product_path:
            noops = NoOps(product_path, dry_run=False, rm_cache=True)

            helm = Helm(noops)

            values = product_path / "noops_workdir/helm/chart/noops"

            # get_values_path
            self.assertEqual(
                helm.get_values_path(),
                values
            )
            self.assertEqual(
                helm.get_values_path("test.yaml"),
                values / "test.yaml"
            )

            # create values directory
            noops.dry_run=True
            self.assertFalse(values.exists())
            helm.create_values_directory()
            self.assertFalse(values.exists())
            noops.dry_run=False

            helm.create_values_directory()
            self.assertTrue(values.exists())

            # create values
            helm.create_values()
            self.assertTrue((values / "values-default.yaml").exists())
            self.assertEqual(
                read_yaml(values / "values-default.yaml"),
                None
            )
            self.assertTrue((values / "values-prod.yaml").exists())
            self.assertEqual(
                read_yaml(values / "values-prod.yaml"),
                {
                    "replicaCount": 2
                }
            )
            self.assertFalse((values / "target-one-cluster-default.yaml").exists())
            self.assertTrue((values / "target-multi-cluster-default.yaml").exists())
            self.assertEqual(
                read_yaml(values / "target-multi-cluster-default.yaml"),
                {
                    "message": "multicluster",
                }
            )
            self.assertTrue((values / "target-multi-cluster-prod.yaml").exists())
            self.assertEqual(
                read_yaml(values / "target-multi-cluster-prod.yaml"),
                {
                    "replicaCount": 1
                }
            )
            self.assertTrue((values / "target-one-cluster.yaml").exists())
            self.assertEqual(
                read_yaml(values / "target-one-cluster.yaml"),
                { "noops": { "target": "one-cluster" } }
            )
            self.assertTrue((values / "target-multi-cluster.yaml").exists())
            self.assertEqual(
                read_yaml(values / "target-multi-cluster.yaml"),
                { "noops": { "target": "multi-cluster" } }
            )
            self.assertTrue((values / "target-active.yaml").exists())
            self.assertEqual(
                read_yaml(values / "target-active.yaml"),
                { "noops": { "target": "active" } }
            )
            self.assertTrue((values / "target-standby.yaml").exists())
            self.assertEqual(
                read_yaml(values / "target-standby.yaml"),
                { "noops": { "target": "standby" } }
            )
            self.assertTrue((values / "profile-default.yaml").exists())
            self.assertEqual(
                read_yaml(values / "profile-default.yaml"),
                {
                    "noops": {
                        "canary": { "enabled": False, "instances": [] },
                        "endpoints": True,
                        "canaryEndpointsOnly": False,
                        "servicesOnly": False
                    }
                }
            )
            self.assertTrue((values / "profile-canary.yaml").exists())
            self.assertEqual(
                read_yaml(values / "profile-canary.yaml"),
                {
                    "noops": { "canary": { "enabled": True }, "endpoints": False }
                }
            )
            self.assertTrue((values / "profile-canary-dedicated-endpoints.yaml").exists())
            self.assertEqual(
                read_yaml(values / "profile-canary-dedicated-endpoints.yaml"),
                {
                    "noops": { "canary": { "enabled": True }}
                }
            )
            self.assertTrue((values / "profile-canary-endpoints-only.yaml").exists())
            self.assertEqual(
                read_yaml(values / "profile-canary-endpoints-only.yaml"),
                {
                    "noops": { "canary": { "enabled": True }, "canaryEndpointsOnly" : True }
                }
            )
            self.assertTrue((values / "profile-services-only.yaml").exists())
            self.assertEqual(
                read_yaml(values / "profile-services-only.yaml"),
                {
                    "noops": { "endpoints": False, "servicesOnly": True }
                }
            )

    def test_helm_values_args(self):
        """Helm values arguments"""

        with product_copy(PRODUCT) as product_path:
            noops = NoOps(product_path, dry_run=False, rm_cache=True)
            prepare(noops)

            values = product_path / "noops_workdir/helm/chart/noops"

            self.assertEqual(
                Helm.helm_values_args("prod", values.parent),
                [
                    '-f',
                    os.fspath(values / "values-default.yaml"),
                    '-f',
                    os.fspath(values / "values-prod.yaml"),
                    '-f',
                    os.fspath(values / "values-svcat.yaml"),
                ]
            )

            self.assertEqual(
                Helm.helm_values_args("test", values.parent),
                [
                    '-f',
                    os.fspath(values / "values-default.yaml"),
                    '-f',
                    os.fspath(values / "values-svcat.yaml"),
                ]
            )

    @patch("noops.package.helm.execute")
    def test_create_package(self, mock_execute):
        """Create Helm Package"""

        with product_copy(PRODUCT) as product_path:
            noops = NoOps(product_path, dry_run=False, rm_cache=True)
            helm = Helm(noops)
            prepare(noops, helm)

            helm.create_package(
                "1.0.0", "127", "New feature", OVERRIDE_TAG)

            self.assertEqual(
                read_yaml(noops.workdir / "helm/chart/Chart.yaml"),
                {
                    'apiVersion': 'v2',
                    'appVersion': '1.0.0',
                    'description': 'New feature',
                    'keywords': [
                        'demo-++1.0.0',
                        'demo-+0.1.0+1.0.0',
                        'demo-127+0.1.0+1.0.0'
                    ],
                    'name': 'demo',
                    'type': 'application',
                    'version': '127+0.1.0'
                }
            )

            self.assertEqual(
                read_yaml(noops.workdir / "helm/chart/noops.yaml"),
                {
                    'apiVersion': 'noops.local/v1alpha1',
                    'kind': 'Chart',
                    'spec': {
                        'package': {
                            'helm': {
                                'pre-processing': ['values.sh']
                            },
                            'supported': None
                        }
                    }
                }
            )

            self.assertEqual(
                read_yaml(noops.workdir / "helm/chart/values.yaml"),
                {
                    "image": "unittest",
                    "tag": "127"
                }
            )

            self.assertEqual(
                mock_execute.call_args_list[0],
                call(
                    'helm',
                    [
                        'package',
                        os.fspath(noops.workdir / "helm/chart"),
                        '-d',
                        os.fspath(noops.workdir)
                    ],
                    dry_run=False
                )
            )

    @patch("noops.package.helm.execute")
    def test_push_package(self, mock_execute):
        """Push Helm Package"""

        with product_copy(PRODUCT) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)
            helm = Helm(noops)

            package = product_path / "noops_workdir/unittest-0.1.0.tgz"
            package.touch()
            directory = product_path / "www"
            directory.mkdir()

            helm.push(directory, "http://repo.local")

            self.assertTrue((directory / "unittest-0.1.0.tgz").exists())

            self.assertEqual(
                mock_execute.call_args_list[0],
                call(
                    'helm',
                    [
                        'repo',
                        'index',
                        os.fspath(directory),
                        '--url',
                        'http://repo.local'
                    ]
                )
            )
