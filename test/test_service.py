#!/usr/bin/env python
import unittest
import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, pkg_root)

from green_box.api import notifications

class TestService(unittest.TestCase):

    def test_extract_uuid_version(self):
        body = {
            'match': {
                'bundle_uuid': 'foo',
                'bundle_version': 'bar'
            }
        }
        uuid, version = notifications.extract_uuid_version(body)
        self.assertEqual(uuid, 'foo')
        self.assertEqual(version, 'bar')

    def test_compose_inputs(self):
        inputs = notifications.compose_inputs('foo', 12, 'baz')
        self.assertEqual(inputs['mock_smartseq2.bundle_uuid'], 'foo')
        self.assertEqual(inputs['mock_smartseq2.bundle_version'], '"12"')
        self.assertEqual(inputs['mock_smartseq2.provenance_script'], 'baz')

    def test_is_authenticated_no_auth_header(self):
        self.assertEquals(notifications.is_authenticated({'foo': 'bar'}, 'baz'), False)

    def test_is_authenticated_wrong_auth_value(self):
        self.assertEquals(notifications.is_authenticated({'auth': 'bar'}, 'foo'), False)

    def test_is_authenticated_valid(self):
        self.assertEquals(notifications.is_authenticated({'auth': 'bar'}, 'bar'), True)

if __name__ == '__main__':
    unittest.main()
