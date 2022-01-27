"""
Tests noops.package.prepare
"""

import shutil
from pathlib import Path
from noops.noops import NoOps
from noops.package.prepare import prepare, embedded_kustomize
from ..test_noops import product_copy, read_yaml_base, read_yaml, write_yaml
from .. import TestCaseNoOps

KUSTOMIZE=Path("tests/data/noops/product/kustomize").resolve()

class Test(TestCaseNoOps):
    """
    Tests noops.package.prepare
    """

    def test_noops_with_kustomize(self):
        """NoOps with kustomize"""

        with product_copy(KUSTOMIZE) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            expected = read_yaml_base(KUSTOMIZE / "tests/noops-generated.yaml", product_path)

            # memory test
            self.assertEqual(
                noops.noops_config,
                expected
            )

    def test_kustomize_copy(self):
        """Copy kustomize in helm chart"""

        with product_copy(KUSTOMIZE) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            helm = noops.workdir / "helm/chart/kustomize"

            self.assertFalse(helm.is_dir())

            embedded_kustomize(noops)

            self.assertTrue(helm.is_dir())
            self.assertTrue((helm / "base/kustomization.yaml").exists())

    def test_kustomize_removed_exists(self):
        """Remove kustomize if target exists"""

        with product_copy(KUSTOMIZE) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            helm = noops.workdir / "helm/chart/kustomize"
            helm.mkdir(exist_ok=True)
            witness = helm / "witness"
            witness.touch()

            self.assertTrue(witness.exists())
            self.assertTrue(helm.is_dir())

            embedded_kustomize(noops)

            self.assertTrue(helm.is_dir())
            self.assertFalse(witness.exists())

    def test_kustomize_unset(self):
        """kustomize not used"""

        with product_copy(KUSTOMIZE) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            noops.noops_config["package"]["helm"]["kustomize"] = None

            embedded_kustomize(noops)

            helm = noops.workdir / "helm/chart/kustomize"
            self.assertFalse(helm.is_dir())

    def test_kustomize_builtin(self):
        """kustomize built-in"""

        with product_copy(KUSTOMIZE) as product_path:
            shutil.move(
                product_path / "devops/helm/kustomize",
                product_path / "devops/helm/chart/kustomize"
            )

            self.assertRaises(
                FileNotFoundError,
                lambda: NoOps(product_path, dry_run=True, rm_cache=True)
            )

            # devops noops.yaml: use a path in helm/chart
            content = read_yaml(product_path / "devops/noops.yaml")
            content["package"]["helm"]["kustomize"]="helm/chart/kustomize"
            write_yaml(product_path / "devops/noops.yaml", content)

            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            embedded_kustomize(noops)

            helm = noops.workdir / "helm/chart/kustomize"
            self.assertTrue(helm.is_dir())

    def test_prepare(self):
        """Prepare helm chart"""

        with product_copy(KUSTOMIZE) as product_path:
            noops = NoOps(product_path, dry_run=False, rm_cache=True)

            prepare(noops)

            svcat_binding = noops.workdir / "helm/chart/noops/values-svcat.yaml"
            self.assertFalse(svcat_binding.exists())

            helm = noops.workdir / "helm/chart/kustomize"
            self.assertTrue(helm.is_dir())

            # with service-catalog enabled
            noops = NoOps(product_path, dry_run=False, rm_cache=True)
            noops.noops_config["features"]["service-catalog"]=True

            prepare(noops)

            svcat_binding = noops.workdir / "helm/chart/noops/values-svcat.yaml"
            self.assertTrue(svcat_binding.exists())

            helm = noops.workdir / "helm/chart/kustomize"
            self.assertTrue(helm.is_dir())
