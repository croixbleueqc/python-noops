"""
Backup working directory to restore it on all tests
"""

import os
from unittest import TestCase

CWD = os.getcwd()

class TestCaseNoOps(TestCase):
    """
    TestCase that can restore working directory

    NoOps.__init__ will change the working directory and broke some tests
    """
    def setUp(self):
        TestCase.setUp(self)
        os.chdir(CWD)
