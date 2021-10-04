"""
Tests relative to noops
"""

import tempfile
import os
from pathlib import Path
import shutil
import subprocess
import json
from contextlib import contextmanager
import yaml
from noops.noops import NoOps
from noops.settings import DEFAULT_WORKDIR
from noops.utils.io import PathEncoder
from . import TestCaseNoOps

DEMO="tests/data/demo"

@contextmanager
def product_copy():
    """
    Temporary Directory with product copy on it
    """
    with tempfile.TemporaryDirectory(prefix="noops-") as tmp:
        product_path = Path(tmp) / "demo"
        shutil.copytree(
            DEMO,
            product_path
        )

        yield product_path

class TestNoOps(TestCaseNoOps):
    """
    Tests relative to NoOps
    """

    def test_noops_local(self):
        """
        Instantiate Noops (local)
        """

        expected_noops_generated_file = Path(
            f"{DEMO}/expected_noops_generated.yaml"
        ).resolve()

        with product_copy() as product_path:

            # Simulate that a cache folder exist
            (product_path / DEFAULT_WORKDIR / "witness").mkdir(parents=True)

            noops = NoOps(product_path, dry_run=True, rm_cache=False)

            # cache purged
            self.assertFalse(
                (product_path / DEFAULT_WORKDIR / "witness").exists()
            )

            # test generated config
            # load expected result
            content = expected_noops_generated_file.read_text(encoding='UTF-8') \
                                                   .replace("{BASE}", os.fspath(product_path))
            expected_config = yaml.load(content, Loader=yaml.SafeLoader)

            # test in memory config
            self.assertEqual(
                json.loads(json.dumps(noops.noops_config, cls=PathEncoder)),
                expected_config
            )

            # test yaml file from the cache
            with noops._get_generated_noops_yaml().open(encoding='UTF-8') as file: # pylint: disable=protected-access
                from_cache = yaml.load(file, Loader=yaml.SafeLoader)
            self.assertEqual(from_cache, expected_config)

            # test json file from the cache
            with noops._get_generated_noops_json().open(encoding='UTF-8') as file: # pylint: disable=protected-access
                from_cache = json.load(file)
            self.assertEqual(from_cache, expected_config)

            # noops environments
            expected_noops_envs = {
                "NOOPS_GENERATED_JSON": noops._get_generated_noops_json(), # pylint: disable=protected-access
                "NOOPS_GENERATED_YAML": noops._get_generated_noops_yaml()  # pylint: disable=protected-access
            }
            self.assertEqual(noops.noops_envs(), expected_noops_envs)

    def test_noops_git(self):
        """
        Instantiate Noops (git)
        """
        with product_copy() as product_path:

            # Use noops with git
            shutil.copyfile(
                f"{DEMO}/noops_git.yaml",
                product_path / "noops.yaml"
            )

            # prepare git devops folder
            devops_path = product_path / "devops"
            subprocess.run("git init .", cwd=devops_path, check=True, shell=True)
            subprocess.run("git add .", cwd=devops_path, check=True, shell=True)
            subprocess.run("git config init.defaultBranch main",
                cwd=devops_path, check=True, shell=True)
            subprocess.run("git commit -m 'devops part'", cwd=devops_path, check=True, shell=True)

            noops = NoOps(product_path, dry_run=True, rm_cache=False)

            self.assertFalse(
                (noops.workdir / ".git").exists()
            )

    def test_product_missing_file(self):
        """
        Test a missing file in product
        """
        with product_copy() as product_path:

            shutil.copyfile(
                f"{DEMO}/noops_missing_file.yaml",
                product_path / "noops.yaml"
            )

            self.assertRaises(
                FileNotFoundError,
                lambda: NoOps(product_path, dry_run=True, rm_cache=False)
            )

    def test_devops_missing_file(self):
        """
        Test a missing file in devops that doesn't exist on product
        """
        with product_copy() as product_path:

            shutil.copyfile(
                f"{DEMO}/devops/noops_missing_file.yaml",
                product_path / "devops" / "noops.yaml"
            )

            self.assertRaises(
                FileNotFoundError,
                lambda: NoOps(product_path, dry_run=True, rm_cache=False)
            )

    def test_dry_run(self):
        """
        Test dry_run
        """
        with product_copy() as product_path:

            noops = NoOps(product_path, dry_run=True, rm_cache=False)
            self.assertTrue(noops.is_dry_run())

            noops = NoOps(product_path, dry_run=False, rm_cache=False)
            self.assertFalse(noops.is_dry_run())

    def test_features(self):
        """
        Test features
        """
        with product_copy() as product_path:

            noops = NoOps(product_path, dry_run=True, rm_cache=False)

            self.assertTrue(noops.is_feature_enabled("service-catalog"))
            self.assertFalse(noops.is_feature_enabled("white-label"))
