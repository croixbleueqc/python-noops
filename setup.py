"""
Setup
"""

#!/usr/bin/env python3
from setuptools import setup, find_packages

with open('README.md', encoding='UTF-8') as file:
    LONG_DESCRIPTION = file.read()

setup(
    name='noops',
    version='1.9.1',
    python_requires='>=3.9',
    packages=find_packages(exclude=['tests']),
    package_data={
        'noops.schema': ['*.yaml']
    },
    install_requires=[
        'pyyaml',
        'pydantic',
        'click',
        'jsonschema'
    ],
    extra_require={
        'dev': [
            'pylint',
            'coverage'
        ]
    },

    scripts=['noopsctl', 'noopsctl.bat', 'noopshpr', 'noopshpr.bat'],

    # Metadata
    author="Croix Bleue du Quebec",
    author_email="devops@qc.croixbleue.ca",
    license="LGPL-3.0-or-later",
    description="NoOps command line utility",
    long_description=LONG_DESCRIPTION,
    url="https://github.com/croixbleueqc/python-noops",
    keywords=["noops", "devops", "git"],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',

        'Operating System :: OS Independent',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    test_suite="tests"
)
