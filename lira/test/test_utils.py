#!/usr/bin/env python
import unittest
from lira import utils as utils


class TestUtils(unittest.TestCase):

    def test_is_authenticated_no_auth_header(self):
        """Request without 'auth' key in header should not be treated as authenticated.
        """
        self.assertFalse(utils.is_authenticated({'foo': 'bar'}, 'baz'))

    def test_is_authenticated_wrong_auth_value(self):
        """Request with wrong auth value(token) in header should not be treated as authenticated.
        """
        self.assertFalse(utils.is_authenticated({'auth': 'bar'}, 'foo'))

    def test_is_authenticated_valid(self):
        """Request with valid auth and token information should be treated as authenticated.
        """
        self.assertTrue(utils.is_authenticated({'auth': 'bar'}, 'bar'))

    def test_extract_uuid_version_subscription_id(self):
        """Test if extract_uuid_version_subscription_id can correctly extract uuid, version
         and subscription from body content."""
        body = {
            'subscription_id': "85test0j-u6y6-uuuu-a90a-kk8",
            'match': {
                'bundle_uuid': 'foo',
                'bundle_version': 'bar'
            }
        }
        uuid, version, subscription_id = utils.extract_uuid_version_subscription_id(body)
        self.assertEqual(uuid, 'foo')
        self.assertEqual(version, 'bar')
        self.assertEqual(subscription_id, "85test0j-u6y6-uuuu-a90a-kk8")

    def test_compose_inputs(self):
        """Test if compose_inputs can correctly create Cromwell inputs file containing bundle uuid and version"""
        inputs = utils.compose_inputs('foo', 'bar', 'baz')
        self.assertEqual(inputs['foo.bundle_uuid'], 'bar')
        self.assertEqual(inputs['foo.bundle_version'], 'baz')


if __name__ == '__main__':
    unittest.main()
