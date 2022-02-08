"""
Tests noops.projects
"""

from unittest.mock import patch
from noops.projects import (
    Projects, ProjectKind, Cluster,
    TargetKind, VersionKind,
    TargetClassesEnum, TargetsEnum)
from noops.utils.io import read_yaml
from . import TestCaseNoOps

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
            kproject.dict(by_alias=True),
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
            result.dict(by_alias=True),
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

        clusters = [ Cluster.parse_obj(i) for i in read_yaml("tests/data/projects/clusters.yaml") ]
        ktarget: TargetKind = TargetKind.parse_obj(
            read_yaml("tests/data/projects/targets.yaml")
        )
        kversion = VersionKind.parse_obj(
            read_yaml("tests/data/projects/versions.yaml")
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
            result.dict(),
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
            result.dict(),
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
            result.dict(),
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
            result.dict(),
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
