"""
Tests noops.projects
"""

from unittest.mock import patch, call
from pathlib import Path
from noops.projects import (
    Projects, ProjectKind, Cluster,
    TargetKind, VersionKind,
    TargetClassesEnum, TargetsEnum,
    ProjectPlanKind)
from noops.utils.io import read_yaml
from . import TestCaseNoOps

DATA=Path("tests/data/projects").resolve()

class Test(TestCaseNoOps):
    """
    Tests noops.projects
    """

    def test_create_projects(self):
        """Create a project"""
        kproject = Projects.create(
            "ns",
            "release",
            "mychart",
            "test",
            cargs=["--set", "replicaCount=0"],
            extra_envs={
                "USER": "Me"
            })

        self.assertEqual(
            kproject.model_dump(by_alias=True),
            {
                'apiVersion': 'noops.local/v1alpha1',
                'kind': 'Project',
                'spec': {
                    'package': {
                        'install': {
                            'chart': 'mychart',
                            'env': 'test',
                            'target': None,
                            'services-only': False,
                            'args': ['--set', 'replicaCount=0'],
                            'envs': {'USER': 'Me'},
                            'white-label': None
                        }
                    },
                    'versions': {'one': None, 'multi': None}
                },
                'metadata': {
                    'name': 'release',
                    'namespace': 'ns'
                }
            }
        )

    def test_create_skeleton_from(self):
        """Create a skeleton project from another one"""

        kproject = ProjectKind(
            metadata={
                "name": "test",
                "namespace": "ns"
            },
            spec={
                "package": {
                    "install": {
                        "chart": "a_chart",
                        "env": "test"
                    },
                    "versions": {
                        "one": {
                            "app_version": "1.0.0"
                        },
                        "multi": [
                            {
                                "app_version": "2.0.0"
                            }
                        ]
                    }
                }
            }
        )

        result = Projects.create_skeleton_from(kproject)

        self.assertEqual(
            result.model_dump(by_alias=True),
            {
                "apiVersion": "noops.local/v1alpha1",
                "kind": "Project",
                "metadata": {
                    "name": "test",
                    "namespace": "ns"
                },
                "spec": {
                    "package": {
                        "install": {
                            "chart": "a_chart",
                            "env": "test",
                            "target": None,
                            "services-only": False,
                            "args": None,
                            "envs": None,
                            "white-label": None
                        }
                    },
                    "versions": {
                        "one": None,
                        "multi": None
                    }
                }
            }
        )

    def test_plan(self):
        """Plan"""

        clusters = [ Cluster.model_validate(i) for i in read_yaml(DATA / "clusters.yaml") ]
        ktarget: TargetKind = TargetKind.model_validate(
            read_yaml(DATA / "targets.yaml")
        )
        kversion = VersionKind.model_validate(
            read_yaml(DATA / "versions.yaml")
        )
        kproject = ProjectKind(
            metadata={
                "name": "test",
                "namespace": "ns"
            },
            spec={
                "package": {
                    "install": {
                        "chart": "a_chart",
                        "env": "test"
                    },
                    "versions": {}
                }
            }
        )

        result = Projects.plan(clusters, ktarget, kversion, kproject)

        self.maxDiff = None # pylint: disable=invalid-name

        # one-cluster
        self.assertEqual(
            result.model_dump(),
            {
                'apiVersion': 'noops.local/v1alpha1',
                'kind': 'ProjectPlan',
                'metadata': {'name': 'test', 'namespace': 'ns'},
                'spec': {
                    'plan': [
                        {
                            'clusters': ['c1'],
                            'template': {
                                'spec': {
                                    'package': {
                                        'install': {
                                            'args': None,
                                            'chart': 'a_chart',
                                            'env': 'test',
                                            'envs': None,
                                            'services_only': False,
                                            'target': TargetsEnum.ONE_CLUSTER,
                                            'white_label': None
                                        }
                                    },
                                    'versions': {
                                        'multi': None,
                                        'one': {
                                            'app_version': '1.0.0',
                                            'args': None,
                                            'build': None,
                                            'version': None
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    'target_class': TargetClassesEnum.ONE_CLUSTER
                }
            }
        )

        # multi-cluster
        ktarget.spec.active.clusterCount = 2
        result = Projects.plan(clusters, ktarget, kversion, kproject)
        self.assertEqual(
            result.model_dump(),
            {
                'apiVersion': 'noops.local/v1alpha1',
                'kind': 'ProjectPlan',
                'metadata': {'name': 'test', 'namespace': 'ns'},
                'spec': {
                    'plan': [
                        {
                            'clusters': ['c1', 'c2'],
                            'template': {
                                'spec': {
                                    'package': {
                                        'install': {
                                            'args': None,
                                            'chart': 'a_chart',
                                            'env': 'test',
                                            'envs': None,
                                            'services_only': False,
                                            'target': TargetsEnum.MULTI_CLUSTER,
                                            'white_label': None
                                        }
                                    },
                                    'versions': {
                                        'multi': None,
                                        'one': {
                                            'app_version': '1.0.0',
                                            'args': None,
                                            'build': None,
                                            'version': None
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    'target_class': TargetClassesEnum.MULTI_CLUSTER
                }
            }
        )

        # active (active/standby)
        ktarget.spec.active.clusterCount = 1
        ktarget.spec.standby.clusterCount = 1
        result = Projects.plan(clusters, ktarget, kversion, kproject)
        self.assertEqual(
            result.model_dump(),
            {
                'apiVersion': 'noops.local/v1alpha1',
                'kind': 'ProjectPlan',
                'metadata': {'name': 'test', 'namespace': 'ns'},
                'spec': {
                    'plan': [
                        {
                            'clusters': ['c1'],
                            'template': {
                                'spec': {
                                    'package': {
                                        'install': {
                                            'args': None,
                                            'chart': 'a_chart',
                                            'env': 'test',
                                            'envs': None,
                                            'services_only': False,
                                            'target': TargetsEnum.ACTIVE,
                                            'white_label': None
                                        }
                                    },
                                    'versions': {
                                        'multi': None,
                                        'one': {
                                            'app_version': '1.0.0',
                                            'args': None,
                                            'build': None,
                                            'version': None
                                        }
                                    }
                                }
                            }
                        },
                        {
                            'clusters': ['c4'],
                            'template': {
                                'spec': {
                                    'package': {
                                        'install': {
                                            'args': None,
                                            'chart': 'a_chart',
                                            'env': 'test',
                                            'envs': None,
                                            'services_only': False,
                                            'target': TargetsEnum.STANDBY,
                                            'white_label': None
                                        }
                                    },
                                    'versions': {
                                        'multi': None,
                                        'one': {
                                            'app_version': '1.0.0',
                                            'args': None,
                                            'build': None,
                                            'version': None
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    'target_class': TargetClassesEnum.ACTIVE_STANDBY
                }
            }
        )

        # services-only
        ktarget.spec.active.clusterCount = 1
        ktarget.spec.standby.clusterCount = 0
        ktarget.spec.services_only.clusterCount = "Remaining"
        result = Projects.plan(clusters, ktarget, kversion, kproject)
        self.assertEqual(
            result.model_dump(),
            {
                'apiVersion': 'noops.local/v1alpha1',
                'kind': 'ProjectPlan',
                'metadata': {'name': 'test', 'namespace': 'ns'},
                'spec': {
                    'plan': [
                        {
                            'clusters': ['c1'],
                            'template': {
                                'spec': {
                                    'package': {
                                        'install': {
                                            'args': None,
                                            'chart': 'a_chart',
                                            'env': 'test',
                                            'envs': None,
                                            'services_only': False,
                                            'target': TargetsEnum.ONE_CLUSTER,
                                            'white_label': None
                                        }
                                    },
                                    'versions': {
                                        'multi': None,
                                        'one': {
                                            'app_version': '1.0.0',
                                            'args': None,
                                            'build': None,
                                            'version': None
                                        }
                                    }
                                }
                            }
                        },
                        {
                            'clusters': ['c2', 'c3', 'c4'],
                            'template': {
                                'spec': {
                                    'package': {
                                        'install': {
                                            'args': None,
                                            'chart': 'a_chart',
                                            'env': 'test',
                                            'envs': None,
                                            'services_only': True,
                                            'target': TargetsEnum.ONE_CLUSTER,
                                            'white_label': None
                                        }
                                    },
                                    'versions': {
                                        'multi': None,
                                        'one': {
                                            'app_version': '1.0.0',
                                            'args': None,
                                            'build': None,
                                            'version': None
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    'target_class': TargetClassesEnum.ONE_CLUSTER
                }
            }
        )

    @patch("noops.package.install.HelmInstall.reconciliation")
    def test_apply_incluster(self, mock_reconciliation):
        """Install the project in the current cluster"""

        pre_processing_path=Path("pre_processing_path")

        kplan: ProjectPlanKind = ProjectPlanKind.model_validate(
            read_yaml(DATA / "projectplan.yaml")
        )
        kproject = ProjectKind(spec=kplan.spec.plan[0].template.spec, metadata=kplan.metadata)
        kprevious = Projects.create_skeleton_from(kproject)

        Projects.apply_incluster(kproject, pre_processing_path, False)

        self.assertEqual(
            mock_reconciliation.call_args_list[0],
            call(kproject, kprevious, pre_processing_path)
        )

    @patch("noops.package.install.HelmInstall.reconciliation")
    def test_delete_incluster(self, mock_reconciliation):
        """Delete the project in the current cluster"""

        kplan: ProjectPlanKind = ProjectPlanKind.model_validate(
            read_yaml(DATA / "projectplan.yaml")
        )
        kproject = ProjectKind(spec=kplan.spec.plan[0].template.spec, metadata=kplan.metadata)
        kempty = Projects.create_skeleton_from(kproject)

        Projects.delete_incluster(kproject, False)

        self.assertEqual(
            mock_reconciliation.call_args_list[0],
            call(kempty, kproject)
        )

    def test_reconciliation_projectplan(self):
        """Reconciliation ProjectPlan"""

        self.maxDiff=None # pylint: disable=invalid-name

        reference = read_yaml(DATA / "projectplan.yaml")

        def copy_reference() -> ProjectPlanKind:
            return ProjectPlanKind.model_validate(reference)

        def project_dict(plan: ProjectPlanKind, index: int) -> dict:
            return ProjectKind(
                spec=plan.spec.plan[index].template.spec,
                metadata=plan.metadata
            ).model_dump()

        current = copy_reference()
        previous = copy_reference()

        # Identical current/previous
        plan = Projects._reconciliation_project_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            [i.model_dump() for i in plan],
            [
                {
                    'cluster': 'c1',
                    'kprevious': project_dict(previous, 0),
                    'kproject': project_dict(previous, 0)
                }
            ]
        )

        # Change in project spec
        current = copy_reference()
        previous = copy_reference()

        current.spec.plan[0].template.spec.versions.one.app_version = '2.0.0'

        plan = Projects._reconciliation_project_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            [i.model_dump() for i in plan],
            [
                {
                    'cluster': 'c1',
                    'kprevious': project_dict(previous, 0), # 1.0.0
                    'kproject': project_dict(current, 0) # 2.0.0
                }
            ]
        )

        # Remove from c1
        current = copy_reference()
        previous = copy_reference()

        current.spec.plan.clear() # remove all deployments

        plan = Projects._reconciliation_project_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            [i.model_dump() for i in plan],
            [
                {
                    'cluster': 'c1',
                    'kprevious': project_dict(previous, 0), # 1.0.0
                    'kproject': None
                }
            ]
        )

        # Add c2, c3
        current = copy_reference()
        previous = copy_reference()

        current.spec.plan[0].clusters.extend(['c2', 'c3'])

        plan = Projects._reconciliation_project_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            [i.model_dump() for i in plan],
            [
                {
                    'cluster': 'c1',
                    'kprevious': project_dict(previous, 0), # 1.0.0
                    'kproject': project_dict(current, 0) # 1.0.0
                },
                {
                    'cluster': 'c2',
                    'kprevious': None,
                    'kproject': project_dict(current, 0)
                },
                {
                    'cluster': 'c3',
                    'kprevious': None,
                    'kproject': project_dict(current, 0)
                }
            ]
        )

        # Replace c1 with c2
        current = copy_reference()
        previous = copy_reference()

        current.spec.plan[0].clusters[0]='c2' # replace c1 with c2

        plan = Projects._reconciliation_project_plan(current, previous) # pylint: disable=protected-access
        self.assertEqual(
            [i.model_dump() for i in plan],
            [
                {
                    'cluster': 'c2',
                    'kprevious': None,
                    'kproject': project_dict(current, 0)
                },
                {
                    'cluster': 'c1',
                    'kprevious': project_dict(previous, 0),
                    'kproject': None
                }
            ]
        )

    @patch("noops.projects.Projects.apply_incluster")
    @patch("noops.projects.Projects.delete_incluster")
    def test_apply(self, mock_delete, mock_apply):
        """Apply the plan"""

        reference = read_yaml(DATA / "projectplan.yaml")
        pre_processing_path = Path("pre_processing_path")

        def copy_reference() -> ProjectPlanKind:
            return ProjectPlanKind.model_validate(reference)

        def get_project(plan: ProjectPlanKind, index: int) -> ProjectKind:
            return ProjectKind(
                spec=plan.spec.plan[index].template.spec,
                metadata=plan.metadata
            )

        # New (no previous state)
        current = copy_reference()
        current.spec.plan[0].clusters.append('c2')

        Projects.apply(current, pre_processing_path, True)

        self.assertEqual(
            mock_apply.call_args_list,
            [
                call(
                    get_project(current, 0),
                    pre_processing_path, True, kprevious=None, cluster='c1'
                ),
                call(
                    get_project(current, 0),
                    pre_processing_path, True, kprevious=None, cluster='c2'
                )
            ]
        )
        self.assertTrue(mock_delete.call_count == 0)
        mock_apply.reset_mock()
        mock_delete.reset_mock()

        # Remove from c2
        current = copy_reference() # c1
        previous = copy_reference()
        previous.spec.plan[0].clusters.append('c2') # c1, c2

        Projects.apply(current, pre_processing_path, True, kpreviousplan=previous)

        self.assertEqual(
            mock_apply.call_args_list,
            [
                call(
                    get_project(current, 0),
                    pre_processing_path, True, kprevious=get_project(previous, 0), cluster='c1'
                )
            ]
        )
        self.assertEqual(
            mock_delete.call_args_list,
            [
                call(
                    get_project(previous, 0),
                    True, cluster='c2'
                )
            ]
        )
        mock_apply.reset_mock()
        mock_delete.reset_mock()
