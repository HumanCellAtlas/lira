#!/usr/bin/env python
import unittest
import lira.api.health as health

class TestService(unittest.TestCase):

    def test_health_check(self):
        self.assertEquals(health.get(), dict(status='healthy'))


if __name__ == '__main__':
    unittest.main()
