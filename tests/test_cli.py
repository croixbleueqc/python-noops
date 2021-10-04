"""
Test relative to cli version
"""

import os
from pathlib import Path
from click.testing import CliRunner
from noops.cli.main import cli
from noops.settings import VERSION
from . import TestCaseNoOps
from .test_noops import product_copy

class TestCli(TestCaseNoOps):
    """
    Test relative to cli version
    """
    def test_cli_version(self):
        """
        noopsctl version
        """
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["version"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, f'version: {VERSION}\n')

    def test_cli_output(self):
        """
        noopsctl output
        """

        output_yaml = Path("tests/data/demo/expected_output.yaml").read_text(encoding='UTF-8')

        with product_copy() as product_path:
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "output"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.output, output_yaml.replace('{BASE}', os.fspath(product_path)))

    def test_cli_pipeline_ci_pr_cd(self):
        """
        noopsctl pipeline (ci,pr,cd)
        """
        with product_copy() as product_path:
            runner = CliRunner()

            # CI
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "ci",
                    "image"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".product.ci").exists())
            (product_path / ".product.ci").unlink()

            # CI - deprecated
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "image",
                    "--ci"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".product.ci").exists())

            # PR
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "pr",
                    "image"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".devops.pr").exists())
            (product_path / ".devops.pr").unlink()

            # PR - deprecated
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "image",
                    "--pr"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".devops.pr").exists())

            # CD
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "cd",
                    "image"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".devops.cd").exists())
            (product_path / ".devops.cd").unlink()

            # CD - deprecated
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "image",
                    "--cd"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".devops.cd").exists())

            # Wrong parameters for deprecated commands
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "image",
                    "--cd",
                    "--ci"
                ]
            )
            self.assertEqual(result.exit_code, 2)
            self.assertTrue(
                "following parameters are mutually exclusive: --ci, --pr, --cd" in result.output
            )

            # Wrong parameters for ci/cd/pr
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "ci",
                    "mytarget"
                ]
            )
            self.assertEqual(result.exit_code, 2)
            self.assertTrue(
                "target 'mytarget' is invalid" in result.output
            )

    def test_cli_pipeline_deploy(self):
        """
        noopsctl pipeline deploy
        """
        with product_copy() as product_path:
            runner = CliRunner()

            # Deploy
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "deploy"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".devops.deploy").exists())

            values_prod = (product_path / "noops_workdir/helm/chart/noops/values-prod.yaml")
            self.assertTrue(values_prod.exists())
            self.assertEqual(values_prod.read_text(encoding='UTF-8'), 'replicasCount: 2\n')

            values_svcat = (product_path / "noops_workdir/helm/chart/noops/values-svcat.yaml")
            self.assertTrue(values_svcat.exists())
            self.assertEqual(values_svcat.read_text(encoding='UTF-8'), 'svcat:\n  bindings: []\n')

            values_default = (product_path / "noops_workdir/helm/chart/noops/values-default.yaml")
            self.assertTrue(values_default.exists())
            self.assertEqual(
                values_default.read_text(encoding='UTF-8'),
                'env:\n  service_version: v1\n'
            )

            target_mc_default = \
                (product_path / "noops_workdir/helm/chart/noops/target-multi-clusters-default.yaml")
            self.assertTrue(target_mc_default.exists())
            self.assertEqual(target_mc_default.read_text(encoding='UTF-8'), 'replicasCount: 1\n')

            # Deploy - Parameters conflict
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "deploy",
                    "--default",
                    "mytarget"
                ]
            )
            self.assertEqual(result.exit_code, 2)
            self.assertTrue(
                "You can NOT use --default and a target" in result.output
            )

            # Deploy - Missing target
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "pipeline",
                    "deploy",
                    "mytarget"
                ]
            )
            self.assertEqual(result.exit_code, 2)
            self.assertTrue(
                "target 'mytarget' is invalid" in result.output
            )

    def test_cli_local(self):
        """
        noopsctl local
        """
        with product_copy() as product_path:
            runner = CliRunner()

            # Local build
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "local",
                    "build"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".devops.local.build").exists())

            # Local run
            result = runner.invoke(
                cli,
                [
                    "-p",
                    os.fspath(product_path),
                    "local",
                    "run"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue((product_path / ".devops.local.run").exists())
