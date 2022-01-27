"""
Tests noops.noops
"""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import shutil
import subprocess
import json
from contextlib import contextmanager
from noops.noops import NoOps
from noops.settings import DEFAULT_WORKDIR
from noops.utils.io import yaml, read_yaml, write_yaml
from . import TestCaseNoOps

MINIMAL=Path("tests/data/noops/product/minimal").resolve()
MINIMAL_GIT=Path("tests/data/noops/product/minimal_git").resolve()
MINIMAL_PROFILE=Path("tests/data/noops/product/minimal_profile").resolve()
SELECTOR=Path("tests/data/noops/product/selector").resolve()

@contextmanager
def product_copy(product: Path):
    """
    Temporary Directory with product copy on it
    """
    with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
        product_path = Path(tmp) / "demo"
        shutil.copytree(
            product,
            product_path
        )

        yield product_path

def read_and_replace_base(file: Path, product_path: Path) -> str:
    """Read a file and replace BASE with product path"""
    return file.read_text(encoding='UTF-8') \
                .replace("{BASE}", os.fspath(product_path))

def read_yaml_base(file_path: Path, product_path: Path) -> dict:
    """
    Read a yaml file and replace BASE
    """
    content = yaml.load(
        read_and_replace_base(file_path, product_path),
        Loader=yaml.SafeLoader)

    return content

def read_json_base(file: Path, product_path: Path) -> dict:
    """Read a json file and replace BASE"""
    return json.loads(
        read_and_replace_base(file, product_path)
    )

def read_json(file: Path) -> dict:
    """Read a json file"""
    return json.loads(
        file.read_text(encoding="UTF-8")
    )

class Test(TestCaseNoOps):
    """
    Tests noops.noops
    """

    def test_minimal(self):
        """Minimal and simple Noops product [local]"""

        with product_copy(MINIMAL) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            expected = read_yaml_base(MINIMAL / "tests" / "noops-generated.yaml", product_path)

            # memory test
            self.assertEqual(
                noops.noops_config,
                expected
            )

            # cache - yaml
            self.assertEqual(
                read_yaml(noops._get_generated_noops_yaml()), # pylint: disable=protected-access
                expected
            )

            # cache - json
            self.assertEqual(
                read_json(noops._get_generated_noops_json()), # pylint: disable=protected-access
                read_json_base(MINIMAL / "tests" / "noops-generated.json", product_path)
            )

            # Noops Environments
            self.assertEqual(
                noops.noops_envs(),
                {
                    "NOOPS_GENERATED_JSON": product_path / DEFAULT_WORKDIR / "noops-generated.json",
                    "NOOPS_GENERATED_YAML": product_path / DEFAULT_WORKDIR / "noops-generated.yaml"
                }
            )

            # Workdir is accurate
            self.assertTrue(
                (product_path / DEFAULT_WORKDIR / "noops.yaml").exists()
            )
            self.assertTrue(
                (product_path / DEFAULT_WORKDIR / "docker/Dockerfile").exists()
            )
            self.assertTrue(
                (product_path / DEFAULT_WORKDIR / "helm/chart").is_dir()
            )
            self.assertTrue(
                (product_path / DEFAULT_WORKDIR / "scripts/deploy.sh").exists()
            )

    def test_minimal_caching(self):
        """Caching workdir"""

        with product_copy(MINIMAL) as product_path:
            _ = NoOps(product_path, dry_run=True, rm_cache=True)

            witness = product_path / DEFAULT_WORKDIR / "witness"
            witness.touch()

            _ = NoOps(product_path, dry_run=True, rm_cache=False)

            self.assertTrue(witness.exists())

            _ = NoOps(product_path, dry_run=True, rm_cache=True)

            self.assertFalse(witness.exists())

            # files missing. forced to generate the cache despite rm_cache=False
            witness.touch()
            noops_generated = product_path / DEFAULT_WORKDIR / "noops-generated.yaml"
            noops_generated.unlink()
            _ = NoOps(product_path, dry_run=True, rm_cache=False)

            self.assertFalse(witness.exists())
            self.assertTrue(noops_generated.exists())

    def test_minimal_git(self):
        """Minimal and simple Noops product [git]"""

        with product_copy(MINIMAL_GIT) as product_path:
            # add devops folder in a local git repo
            devops_path = product_path / "devops"
            subprocess.run("git init .", cwd=devops_path, check=True, shell=True)
            subprocess.run("git add .", cwd=devops_path, check=True, shell=True)
            subprocess.run("git config init.defaultBranch main",
                cwd=devops_path, check=True, shell=True)
            subprocess.run("git commit -m 'devops part'", cwd=devops_path, check=True, shell=True)

            self.assertTrue((devops_path / ".git").is_dir())

            noops = NoOps(product_path, dry_run=True, rm_cache=False)

            self.assertFalse((noops.workdir / ".git").exists())

    def test_minimal_profile(self):
        """Minimal and simple Noops product with profile"""

        with product_copy(MINIMAL_PROFILE) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            expected = read_yaml_base(
                MINIMAL_PROFILE / "tests" / "noops-generated.yaml", product_path)

            # memory test
            self.assertEqual(
                noops.noops_config,
                expected
            )

            # cache - yaml
            self.assertEqual(
                read_yaml(noops._get_generated_noops_yaml()), # pylint: disable=protected-access
                expected
            )

            # cache - json
            self.assertEqual(
                read_json(noops._get_generated_noops_json()), # pylint: disable=protected-access
                read_json_base(MINIMAL_PROFILE / "tests" / "noops-generated.json", product_path)
            )

    def test_minimal_no_local_git(self):
        """NoOps without devops.local and devops.git set"""
        with product_copy(MINIMAL) as product_path:

            # remove devops.local key from noops.yaml
            content = read_yaml(product_path / "noops.yaml")
            _ = content["devops"].pop("local")
            write_yaml(product_path / "noops.yaml", content)

            self.assertRaises(
                ValueError,
                lambda: NoOps(product_path, dry_run=True, rm_cache=False)
            )

    @patch('builtins.print')
    def test_output(self, mock_print): # pylint: disable=no-self-use
        """Output noops.yaml"""
        with product_copy(MINIMAL) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=False)

            noops.output()
            mock_print.assert_called_with(
                "devops:\n  local:\n    path: devops\nmetadata:\n  version: 1\npackage:\n  docker:\n    app:\n      dockerfile: !path '{BASE}/docker/Dockerfile'\n  helm:\n    chart: !path '{BASE}/helm/chart'\n    values: !path '{BASE}/helm/chart/noops'\npipeline:\n  deploy:\n    default: !path '{BASE}/scripts/deploy.sh'\n" \
                    .format(BASE=os.fspath(noops.workdir)) # pylint: disable=line-too-long
            )

            noops.output(asjson=True)
            mock_print.assert_called_with(
                '{\n  "metadata": {\n    "version": 1\n  },\n  "package": {\n    "docker": {\n      "app": {\n        "dockerfile": "{BASE}/docker/Dockerfile"\n      }\n    },\n    "helm": {\n      "chart": "{BASE}/helm/chart",\n      "values": "{BASE}/helm/chart/noops"\n    }\n  },\n  "pipeline": {\n    "deploy": {\n      "default": "{BASE}/scripts/deploy.sh"\n    }\n  },\n  "devops": {\n    "local": {\n      "path": "devops"\n    }\n  }\n}' \
                    .replace("{BASE}", os.fspath(noops.workdir)) # pylint: disable=line-too-long
            )

    def test_dry_run(self):
        """dry_run"""

        with product_copy(MINIMAL) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=False)
            self.assertTrue(noops.is_dry_run())

            noops = NoOps(product_path, dry_run=False, rm_cache=False)
            self.assertFalse(noops.is_dry_run())

    def test_features(self):
        """Features"""

        with product_copy(MINIMAL) as product_path:

            noops = NoOps(product_path, dry_run=True, rm_cache=False)

            self.assertTrue(noops.is_feature_enabled("service-catalog"))
            self.assertFalse(noops.is_feature_enabled("white-label"))

    def test_missing_devops(self):
        """Missing DevOps file refered by devops noops.yaml"""

        with product_copy(SELECTOR) as product_path:

            # remove devops file
            (product_path / "devops/docker/Dockerfile").unlink()

            self.assertRaises(
                FileNotFoundError,
                lambda: NoOps(product_path, dry_run=True, rm_cache=False)
            )

    def test_missing_product(self):
        """Missing Product file refered by product noops.yaml"""

        with product_copy(SELECTOR) as product_path:

            # remove devops file
            (product_path / "deploy.sh").unlink()

            self.assertRaises(
                FileNotFoundError,
                lambda: NoOps(product_path, dry_run=True, rm_cache=False)
            )

    def test_product_in_devops(self):
        """Alternative DevOps file set in product (does not exist in product)"""

        with product_copy(SELECTOR) as product_path:

            content = read_yaml(product_path / "noops.yaml")
            content["package"] = {
                "docker": {
                    "app": {
                        "dockerfile": "docker/Dockerfile.distroless"
                    }
                }
            }
            write_yaml(product_path / "noops.yaml", content)

            noops = NoOps(product_path, dry_run=True, rm_cache=False)

            self.assertEqual(
                noops.noops_config["package"]["docker"]["app"]["dockerfile"],
                noops.workdir / "docker/Dockerfile.distroless"
            )

    def test_product_profile(self):
        """Use a product file set in product profiles"""

        with product_copy(SELECTOR) as product_path:

            # use local profile
            content = read_yaml(product_path / "noops.yaml")
            content["profile"] = "local"
            write_yaml(product_path / "noops.yaml", content)

            noops = NoOps(product_path, dry_run=True, rm_cache=False)

            self.assertEqual(
                noops.noops_config["pipeline"]["deploy"]["default"],
                product_path / "deploy.sh"
            )
