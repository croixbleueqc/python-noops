"""
Tests noops.pipeline.deploy
"""

from unittest.mock import patch, call
from pathlib import Path
from noops.noops import NoOps
from noops.pipeline.deploy import pipeline_deploy
from ..test_noops import product_copy, read_yaml_base, read_yaml, write_yaml
from .. import TestCaseNoOps

DEPLOY=Path("tests/data/pipeline/deploy").resolve()

class Test(TestCaseNoOps):
    """
    Tests noops.pipeline.deploy
    """

    def test_noops(self):
        """NoOps with White-label"""

        with product_copy(DEPLOY) as product_path:
            noops = NoOps(product_path, dry_run=True, rm_cache=True)

            expected = read_yaml_base(DEPLOY / "tests/noops-generated.yaml", product_path)

            # memory test
            self.assertEqual(
                noops.noops_config,
                expected
            )

    @patch("noops.pipeline.deploy.execute")
    def test_deploy_labels(self, mock_execute):
        """Deploy all labels [white-label]"""

        with product_copy(DEPLOY) as product_path:
            noops = NoOps(product_path, dry_run=False, rm_cache=True)

            pipeline_deploy(noops, "default", ["--fake"])

            self.assertEqual(mock_execute.call_count, 2)

            self.assertEqual(
                mock_execute.call_args_list[1],
                call(
                    noops.workdir / "scripts/deploy.sh",
                    ['--fake'],
                    extra_envs={
                        'NOOPS_GENERATED_JSON': noops.workdir / "noops-generated.json",
                        'NOOPS_GENERATED_YAML': noops.workdir / "noops-generated.yaml",
                        'NOOPS_WHITE_LABEL': 'y',
                        'NOOPS_WHITE_LABEL_REBRAND': 'test2',
                        'NOOPS_WHITE_LABEL_MARKETER': 'Test2 Inc'
                    },
                    dry_run=False
                )
            )

    @patch("noops.pipeline.deploy.execute")
    def test_deploy_regular(self, mock_execute):
        """Deploy without labels [regular]"""

        with product_copy(DEPLOY) as product_path:

            # disable white-label feature
            content = read_yaml(product_path / "noops.yaml")
            content["features"]["white-label"]=False
            write_yaml(product_path / "noops.yaml", content)

            noops = NoOps(product_path, dry_run=False, rm_cache=True)

            pipeline_deploy(noops, "default", ["--fake"])

            self.assertEqual(mock_execute.call_count, 1)

            self.assertEqual(
                mock_execute.call_args_list[0],
                call(
                    noops.workdir / "scripts/deploy.sh",
                    ['--fake'],
                    {
                        'NOOPS_GENERATED_JSON': noops.workdir / "noops-generated.json",
                        'NOOPS_GENERATED_YAML': noops.workdir / "noops-generated.yaml"
                    },
                    dry_run=False
                )
            )
