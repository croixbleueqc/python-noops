"""
Tests noops.package.install
"""

import tempfile
import os
from unittest.mock import patch, call
from pathlib import Path
from noops.package.install import HelmInstall
from noops.typing.versions import MultiSpec
from noops.typing.projects import ProjectKind, WhiteLabelSpec
from noops.typing.profiles import ProfileEnum
from noops.typing.targets import TargetsEnum
from noops.errors import KustomizeStructure
from .. import TestCaseNoOps
from ..test_noops import read_yaml

DATA=Path("tests/data/package/install").resolve()

class Test(TestCaseNoOps):
    """
    Tests noops.package.install
    """
    def test_init(self):
        """Init HelmInstall"""
        helm = HelmInstall(True)
        self.assertTrue(helm.dry_run)
        self.assertEqual(helm.global_flags(), [])

        helm = HelmInstall(False)
        self.assertFalse(helm.dry_run)
        self.assertEqual(helm.global_flags(), [])

        helm = HelmInstall(False, "unittest")
        self.assertEqual(helm.global_flags(), ['--kube-context', 'unittest'])

    @patch("noops.package.install.execute")
    def test_update(self, mock_execute):
        """Update helm repo"""

        HelmInstall.update()

        self.assertEqual(
            mock_execute.call_args_list[0],
            call('helm', ['repo', 'update'], capture_output=True)
        )

    @patch("noops.package.install.execute")
    def test_pull(self, mock_execute):
        """Pull from helm repo"""

        pkg = HelmInstall.pull(
            {
                "name": "repo/demo",
                "version": "1.0.0"
            },
            Path("/store/chart/to")
        )

        self.assertEqual(pkg, Path("/store/chart/to/demo"))

        self.assertEqual(
            mock_execute.call_args_list[0],
            call(
                'helm',
                [
                    'pull', 'repo/demo',
                    '--version', '1.0.0',
                    '--untar', '--untardir', "/store/chart/to"
                ], capture_output=True)
        )

    @patch("noops.package.install.execute")
    def test_uninstall(self, mock_execute):
        """Uninstall helm releases"""

        HelmInstall(False).uninstall("ns", "demo")

        self.assertEqual(
            mock_execute.call_args_list[0],
            call(
                'helm', ['uninstall', 'demo', '--namespace', 'ns'],
                dry_run=False, capture_output=True)
        )

    @patch("noops.package.install.execute")
    def test_uninstall_context(self, mock_execute):
        """Uninstall helm releases for a kube context"""

        HelmInstall(False, "unittest").uninstall("ns", "demo")

        self.assertEqual(
            mock_execute.call_args_list[0],
            call(
                'helm', ['uninstall', 'demo', '--namespace', 'ns', '--kube-context', 'unittest'],
                dry_run=False, capture_output=True)
        )

    def test_canary_weight(self):
        """Canary weight"""

        self.assertEqual(
            len(HelmInstall._helm_canary_weight("noops.canary.weight", None)), # pylint: disable=protected-access
            0
        )

        self.assertEqual(
            HelmInstall._helm_canary_weight("noops.canary.weight", 10), # pylint: disable=protected-access
            [
                '--set', 'noops.canary.weight=10'
            ]
        )

    def test_reorder(self):
        """Reorder an unordered sub list of an another one"""

        self.assertEqual(
            HelmInstall._reorder([3,5], [1,2,5,3,9]), # pylint: disable=protected-access
            [5,3]
        )

    def test_canary_versions(self):
        """Canary versions involved"""
        self.assertIsNone(
            HelmInstall._helm_canary_versions("noops.canary.instances", []), # pylint: disable=protected-access
        )

        self.assertEqual(
            HelmInstall._helm_canary_versions( # pylint: disable=protected-access
                "noops.canary.instances",
                [
                    MultiSpec(app_version="1.0.0", weight=10),
                    MultiSpec(app_version="2.0.0", weight=90),
                ]
            ),
            [
                '--set',
                'noops.canary.instances[0].app_version=1.0.0',
                '--set',
                'noops.canary.instances[0].weight=10',
                '--set',
                'noops.canary.instances[1].app_version=2.0.0',
                '--set',
                'noops.canary.instances[1].weight=90'
            ]
        )

    def test_reconciliation_plan(self): # pylint: disable=too-many-statements
        """Reconciliation Plan"""

        self.maxDiff=None # pylint: disable=invalid-name

        reference = {
            "metadata": {
                "name": "test",
                "namespace": "ns"
            },
            "spec": {
                "package": {
                    "install": {
                        "chart": "a_chart",
                        "env": "test"
                    }
                },
                "versions": {
                    "one": {
                        "app_version": "1.0.0"
                    },
                    "multi": [
                        {
                            "app_version": "2.0.0"
                        },
                        {
                            "app_version": "3.0.0"
                        }
                    ]
                }
            }
        }

        def copy_reference() -> ProjectKind:
            return ProjectKind.model_validate(reference)

        current = copy_reference()
        previous = copy_reference()

        # Identical current/previous
        plan = HelmInstall._reconciliation_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            plan.model_dump(),
            {
                'added': [],
                'canary_versions': None,
                'changed': [],
                'removed': [],
                'removed_canary': False
            }
        )

        # Package spec changes -> force to redeploy all
        current = copy_reference()
        previous = copy_reference()
        current.spec.package.install.envs = {"ENV":"test"}

        plan = HelmInstall._reconciliation_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            plan.model_dump(),
            {
                'added': [],
                'canary_versions': None,
                'changed': [
                    {
                        "app_version": "1.0.0",
                        "args": None,
                        "build": None,
                        "version": None
                    },
                    {
                        "app_version": "2.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": None
                    },
                    {
                        "app_version": "3.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": None
                    }
                ],
                'removed': [],
                'removed_canary': False
            }
        )

        # Remove all versions
        current = copy_reference()
        previous = copy_reference()
        current.spec.versions.one = None
        current.spec.versions.multi = None

        plan = HelmInstall._reconciliation_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            plan.model_dump(),
            {
                'added': [],
                'canary_versions': None,
                'changed': [],
                'removed': [
                    {
                        "app_version": "1.0.0",
                        "args": None,
                        "build": None,
                        "version": None
                    },
                    {
                        "app_version": "2.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": None
                    },
                    {
                        "app_version": "3.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": None
                    }
                ],
                'removed_canary': False
            }
        )

        # Add versions
        current = copy_reference()
        previous = copy_reference()
        previous.spec.versions.one = None
        previous.spec.versions.multi = None

        plan = HelmInstall._reconciliation_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            plan.model_dump(),
            {
                'added': [
                    {
                        "app_version": "1.0.0",
                        "args": None,
                        "build": None,
                        "version": None
                    },
                    {
                        "app_version": "2.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": None
                    },
                    {
                        "app_version": "3.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": None
                    }
                ],
                'canary_versions': None,
                'changed': [],
                'removed': [],
                'removed_canary': False
            }
        )

        # Change versions
        current = copy_reference()
        previous = copy_reference()
        current.spec.versions.one.args=['--set', 'fix=123']
        current.spec.versions.multi[1].args=['--set', 'fix=321']

        plan = HelmInstall._reconciliation_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            plan.model_dump(),
            {
                'added': [],
                'canary_versions': None,
                'changed': [
                    {
                        "app_version": "1.0.0",
                        "args": ['--set', 'fix=123'],
                        "build": None,
                        "version": None
                    },
                    {
                        "app_version": "3.0.0",
                        "args": ['--set', 'fix=321'],
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": None
                    }
                ],
                'removed': [],
                'removed_canary': False
            }
        )

        # Remove One, Change Multi for Canary
        current = copy_reference()
        previous = copy_reference()
        current.spec.versions.one = None
        current.spec.versions.multi[0].weight = 10
        current.spec.versions.multi[1].weight = 90

        plan = HelmInstall._reconciliation_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            plan.model_dump(),
            {
                'added': [],
                'canary_versions': [
                    {
                        "app_version": "2.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 10
                    },
                    {
                        "app_version": "3.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 90
                    }
                ],
                'changed': [
                    {
                        "app_version": "2.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 10
                    },
                    {
                        "app_version": "3.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 90
                    }
                ],
                'removed': [
                    {
                        "app_version": "1.0.0",
                        "args": None,
                        "build": None,
                        "version": None
                    }
                ],
                'removed_canary': False
            }
        )

        # Canary changes (new weight)
        current = copy_reference()
        previous = copy_reference()
        previous.spec.versions.one = None
        previous.spec.versions.multi[0].weight = 40
        previous.spec.versions.multi[1].weight = 60
        current.spec.versions.one = None
        current.spec.versions.multi[0].weight = 10
        current.spec.versions.multi[1].weight = 90

        plan = HelmInstall._reconciliation_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            plan.model_dump(),
            {
                'added': [],
                'canary_versions': [
                    {
                        "app_version": "2.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 10
                    },
                    {
                        "app_version": "3.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 90
                    }
                ],
                'changed': [
                    {
                        "app_version": "2.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 10
                    },
                    {
                        "app_version": "3.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 90
                    }
                ],
                'removed': [],
                'removed_canary': False
            }
        )

        # Canary changes (not used anymore)
        current = copy_reference()
        previous = copy_reference()
        previous.spec.versions.one = None
        previous.spec.versions.multi[0].weight = 40
        previous.spec.versions.multi[1].weight = 60
        current.spec.versions.one = None
        current.spec.versions.multi = None

        plan = HelmInstall._reconciliation_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            plan.model_dump(),
            {
                'added': [],
                'canary_versions': None,
                'changed': [],
                'removed': [
                    {
                        "app_version": "2.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 40
                    },
                    {
                        "app_version": "3.0.0",
                        "args": None,
                        "build": None,
                        "dedicated_endpoints": None,
                        "version": None,
                        "weight": 60
                    }
                ],
                'removed_canary': True
            }
        )

    @patch("noops.package.install.HelmInstall.upgrade")
    def test_reconciliation_upgrade(self, mock_upgrade):
        """Reconciliation Upgrade"""

        reference = {
            "metadata": {
                "name": "test",
                "namespace": "ns"
            },
            "spec": {
                "package": {
                    "install": {
                        "chart": "a_chart",
                        "env": "test",
                        "envs": {
                            "ENV": "unittest"
                        },
                        "target": "one-cluster"
                    }
                },
                "versions": {
                    "one": {
                        "app_version": "1.0.0"
                    }
                }
            }
        }

        preprocessing = Path("/path/to/preprocessing")
        helm = HelmInstall(True)
        kproject : ProjectKind = ProjectKind.model_validate(reference)

        # reference case
        helm._reconciliation_upgrade( # pylint: disable=protected-access
            "ns", "demo", kproject.spec.package.install,
            kproject.spec.versions.one, preprocessing)
        self.assertEqual(
            mock_upgrade.call_args_list[0],
            call(
                'ns', 'demo', 'a_chart-++1.0.0', 'test', preprocessing,
                [ProfileEnum.DEFAULT], [],
                {'ENV': 'unittest'}, TargetsEnum.ONE_CLUSTER
            )
        )
        mock_upgrade.reset_mock()

        # + cargs + build
        kproject.spec.versions.one.build=127
        helm._reconciliation_upgrade( # pylint: disable=protected-access
            "ns", "demo", kproject.spec.package.install,
            kproject.spec.versions.one, preprocessing, cargs=["-y"])
        self.assertEqual(
            mock_upgrade.call_args_list[0],
            call(
                'ns', 'demo', 'a_chart-127++1.0.0', 'test', preprocessing,
                [ProfileEnum.DEFAULT], ["-y"],
                {'ENV': 'unittest'}, TargetsEnum.ONE_CLUSTER
            )
        )
        mock_upgrade.reset_mock()

        # + version + install.args
        kproject.spec.versions.one.version="0.1.0"
        kproject.spec.package.install.args=["-i"]
        helm._reconciliation_upgrade( # pylint: disable=protected-access
            "ns", "demo", kproject.spec.package.install,
            kproject.spec.versions.one, preprocessing, cargs=["-y"])
        self.assertEqual(
            mock_upgrade.call_args_list[0],
            call(
                'ns', 'demo', 'a_chart-127+0.1.0+1.0.0', 'test', preprocessing,
                [ProfileEnum.DEFAULT], ["-y", "-i"],
                {'ENV': 'unittest'}, TargetsEnum.ONE_CLUSTER
            )
        )
        mock_upgrade.reset_mock()

        # + version.args
        kproject.spec.versions.one.args=["-v"]
        helm._reconciliation_upgrade( # pylint: disable=protected-access
            "ns", "demo", kproject.spec.package.install,
            kproject.spec.versions.one, preprocessing, cargs=["-y"])
        self.assertEqual(
            mock_upgrade.call_args_list[0],
            call(
                'ns', 'demo', 'a_chart-127+0.1.0+1.0.0', 'test', preprocessing,
                [ProfileEnum.DEFAULT], ["-y", "-i", "-v"],
                {'ENV': 'unittest'}, TargetsEnum.ONE_CLUSTER
            )
        )
        mock_upgrade.reset_mock()

        # + profile override
        helm._reconciliation_upgrade( # pylint: disable=protected-access
            "ns", "demo", kproject.spec.package.install,
            kproject.spec.versions.one, preprocessing, cargs=["-y"],
            override_profiles=[ProfileEnum.CANARY])
        self.assertEqual(
            mock_upgrade.call_args_list[0],
            call(
                'ns', 'demo', 'a_chart-127+0.1.0+1.0.0', 'test', preprocessing,
                [ProfileEnum.CANARY], ["-y", "-i", "-v"],
                {'ENV': 'unittest'}, TargetsEnum.ONE_CLUSTER
            )
        )
        mock_upgrade.reset_mock()

        # + services-only
        kproject.spec.package.install.services_only=True
        helm._reconciliation_upgrade( # pylint: disable=protected-access
            "ns", "demo", kproject.spec.package.install,
            kproject.spec.versions.one, preprocessing, cargs=["-y"],
            override_profiles=[ProfileEnum.CANARY])
        self.assertEqual(
            mock_upgrade.call_args_list[0],
            call(
                'ns', 'demo', 'a_chart-127+0.1.0+1.0.0', 'test', preprocessing,
                [ProfileEnum.CANARY, ProfileEnum.SERVICES_ONLY], ["-y", "-i", "-v"],
                {'ENV': 'unittest'}, TargetsEnum.ONE_CLUSTER
            )
        )
        mock_upgrade.reset_mock()

        # + white-label
        kproject.spec.package.install.white_label=WhiteLabelSpec(
            rebrand="test1",
            marketer="Test1 Inc"
        )
        helm._reconciliation_upgrade( # pylint: disable=protected-access
            "ns", "demo", kproject.spec.package.install,
            kproject.spec.versions.one, preprocessing, cargs=["-y"],
            override_profiles=[ProfileEnum.CANARY])
        self.assertEqual(
            mock_upgrade.call_args_list[0],
            call(
                'ns', 'demo', 'a_chart-127+0.1.0+1.0.0', 'test', preprocessing,
                [ProfileEnum.CANARY, ProfileEnum.SERVICES_ONLY],
                [
                    '-y', '-i', '-v',
                    '--set', 'noops.white-label.enabled=true',
                    '--set', 'noops.white-label.rebrand=test1',
                    '--set', 'noops.white-label.marketer=Test1 Inc'
                ],
                {'ENV': 'unittest'}, TargetsEnum.ONE_CLUSTER
            )
        )
        mock_upgrade.reset_mock()

    @patch("noops.package.install.HelmInstall.uninstall")
    def test_reconciliation_uninstall(self, mock_uninstall):
        """Reconciliation Uninstall"""

        HelmInstall(False)._reconciliation_uninstall("ns", "demo-") # pylint: disable=protected-access
        self.assertEqual(
            mock_uninstall.call_args_list[0],
            call('ns', 'demo')
        )

    def test_kustomize(self):
        """Kustomize for Helm Post-Renderer"""
        kustomize0 = DATA / "kustomize0"
        kustomize1 = DATA / "kustomize1"
        kustomize2 = DATA / "kustomize2"
        kustomize3 = DATA / "kustomize3"

        with tempfile.TemporaryDirectory(prefix="noops-") as tmpdir:
            os.chdir(os.fspath(tmpdir))
            os.mkdir("noops_workdir")
            hpr = Path(tmpdir) / "noops_workdir/noopshpr.yaml"

            # kustomize does not exist
            self.assertEqual(
                HelmInstall._kustomize(kustomize0, "unittest"), # pylint: disable=protected-access
                ([],[])
            )
            self.assertFalse(hpr.exists())

            # kustomize with base only
            self.assertEqual(
                HelmInstall._kustomize(kustomize1, "unittest"), # pylint: disable=protected-access
                (
                    ['--post-renderer', 'noopshpr'],
                    ['-k', os.fspath(kustomize1 / "kustomize/base")]
                )
            )
            self.assertTrue(hpr.exists())
            self.assertEqual(
                read_yaml(hpr),
                {
                    "base": kustomize1 / "kustomize/base",
                    "kustomize": kustomize1 / "kustomize/base"
                }
            )

            # kustomize with base AND env (unittest)
            self.assertEqual(
                HelmInstall._kustomize(kustomize2, "unittest"), # pylint: disable=protected-access
                (
                    ['--post-renderer', 'noopshpr'],
                    [
                        '-k', os.fspath(kustomize2 / "kustomize/base"),
                        '-k', os.fspath(kustomize2 / "kustomize/unittest")
                    ]
                )
            )
            self.assertTrue(hpr.exists())
            self.assertEqual(
                read_yaml(hpr),
                {
                    "base": kustomize2 / "kustomize/base",
                    "kustomize": kustomize2 / "kustomize/unittest"
                }
            )

            # kustomize with env BUT not base
            self.assertRaises(
                KustomizeStructure,
                lambda: HelmInstall._kustomize(kustomize3, "unittest") # pylint: disable=protected-access
            )

    @patch("noops.package.install.HelmInstall._reconciliation_uninstall")
    @patch("noops.package.install.HelmInstall._reconciliation_upgrade")
    def test_reconciliation(self, mock_upgrade, mock_uninstall):
        """Reconciliation [public]"""

        self.maxDiff=None # pylint: disable=invalid-name

        # IMPORTANT:
        # this reference is inaccurate as Canary and One can't be used together
        # this is just to simplify this unittest
        reference = {
            "metadata": {
                "name": "test",
                "namespace": "ns"
            },
            "spec": {
                "package": {
                    "install": {
                        "chart": "a_chart",
                        "env": "test"
                    }
                },
                "versions": {
                    "one": {
                        "app_version": "1.0.0"
                    },
                    "multi": [
                        {
                            "app_version": "2.0.0",
                            "weight": 10
                        },
                        {
                            "app_version": "3.0.0",
                            "weight": 90
                        }
                    ]
                }
            }
        }

        def copy_reference() -> ProjectKind:
            return ProjectKind.model_validate(reference)

        preprocessing = Path("/path/to/preprocessing")
        helm = HelmInstall(True)

        # Remove One, Multi and Add new multi (keep canary)
        project = copy_reference()
        previous = copy_reference()
        project.spec.versions.one = None
        project.spec.versions.multi[1].app_version="4.0.0"

        helm.reconciliation(project, previous, pre_processing_path=preprocessing)
        self.assertEqual(
            mock_uninstall.call_args_list,
            [
                call('ns', 'test'), # remove one
                call('ns', 'test-3.0.0') # remove release 3
            ]
        )
        self.assertEqual(
            mock_upgrade.call_args_list,
            [
                call( # add version 4.0.0
                    'ns', 'test-4.0.0', project.spec.package.install,
                    project.spec.versions.multi[1],
                    preprocessing,
                    cargs=['--set', 'noops.canary.weight=90']
                ),
                call( # upgrade canary endpoint
                    'ns', 'test', project.spec.package.install, project.spec.versions.multi[-1],
                    preprocessing,
                    override_profiles=[ProfileEnum.DEFAULT, ProfileEnum.CANARY_ENDPOINTS_ONLY],
                    cargs=[
                        '--set', 'noops.canary.instances[0].app_version=2.0.0',
                        '--set', 'noops.canary.instances[0].weight=10',
                        '--set', 'noops.canary.instances[1].app_version=4.0.0',
                        '--set', 'noops.canary.instances[1].weight=90'
                    ]
                )
            ]
        )
        mock_upgrade.reset_mock()
        mock_uninstall.reset_mock()

        # Remove canary
        project = copy_reference()
        previous = copy_reference()
        project.spec.versions.multi = None

        helm.reconciliation(project, previous)
        self.assertEqual(
            mock_uninstall.call_args_list,
            [
                call('ns', 'test-2.0.0'), # remove release 2
                call('ns', 'test-3.0.0'), # remove release 3
                call('ns', 'test') # remove canary endpoint
            ]
        )
        self.assertEqual(
            mock_upgrade.call_count,
            0
        )
        mock_upgrade.reset_mock()
        mock_uninstall.reset_mock()

        # Change One (no multi involved)
        project = copy_reference()
        previous = copy_reference()
        project.spec.versions.multi = None
        previous.spec.versions.multi = None
        previous.spec.versions.one.version="0.0.1"

        helm.reconciliation(project, previous)
        self.assertEqual(
            mock_upgrade.call_args_list,
            [
                call(
                    'ns', 'test', project.spec.package.install, project.spec.versions.one,
                    None
                )
            ]
        )
        self.assertEqual(
            mock_uninstall.call_count,
            0
        )
        mock_upgrade.reset_mock()
        mock_uninstall.reset_mock()

        # Add and remove multi version (no canary)
        project = copy_reference()
        previous = copy_reference()
        project.spec.versions.multi[0].weight=None
        project.spec.versions.multi[1].weight=None
        project.spec.versions.multi[1].app_version="5.0.0"
        project.spec.versions.one=None
        previous.spec.versions.multi[0].weight=None
        previous.spec.versions.multi[1].weight=None
        previous.spec.versions.one=None

        helm.reconciliation(project, previous)
        self.assertEqual(
            mock_upgrade.call_args_list,
            [
                call(
                    'ns', 'test-5.0.0', project.spec.package.install,
                    project.spec.versions.multi[1],
                    None, cargs=[]
                )
            ]
        )
        self.assertEqual(
            mock_uninstall.call_args_list,
            [
                call('ns', 'test-3.0.0')
            ]
        )
        mock_upgrade.reset_mock()
        mock_uninstall.reset_mock()
