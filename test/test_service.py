#!/usr/bin/env python
import unittest
import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, pkg_root)

import green_box.api as api


class TestService(unittest.TestCase):

    def test_health_check(self):
        self.assertEquals(api.health.get(), dict(status='healthy'))


if __name__ == '__main__':
    unittest.main()
