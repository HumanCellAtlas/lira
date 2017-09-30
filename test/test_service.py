#!/usr/bin/env python
import unittest
import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, pkg_root)

import green_box.api as api


class TestService(unittest.TestCase):

    def test_extract_uuid_version(self):
        body = {
            'subscription_id': 222,
            'match': {
                'bundle_uuid': 'foo',
                'bundle_version': 'bar'
            }
        }
        uuid, version, subscription_id = api.notifications.extract_uuid_version_subscription_id(body)
        self.assertEqual(uuid, 'foo')
        self.assertEqual(version, 'bar')
        self.assertEqual(subscription_id, 222)

    def test_compose_inputs(self):
        inputs = api.notifications.compose_inputs('foo', 'bar', 'baz')
        self.assertEqual(inputs['foo.bundle_uuid'], 'bar')
        self.assertEqual(inputs['foo.bundle_version'], 'baz')

    def test_is_authenticated_no_auth_header(self):
        self.assertEquals(api.notifications.is_authenticated({'foo': 'bar'}, 'baz'), False)

    def test_is_authenticated_wrong_auth_value(self):
        self.assertEquals(api.notifications.is_authenticated({'auth': 'bar'}, 'foo'), False)

    def test_is_authenticated_valid(self):
        self.assertEquals(api.notifications.is_authenticated({'auth': 'bar'}, 'bar'), True)

    def test_health_check(self):
        self.assertEquals(api.health.get(), dict(status='healthy'))

if __name__ == '__main__':
    unittest.main()
