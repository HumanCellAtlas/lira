#!/usr/bin/env python
import unittest
from lira import lira_utils


class TestUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.valid_github_url = 'https://github.com/Organization/Repo/blob/master/lib/utils/util.py'
        cls.valid_github_raw_url = 'https://raw.githubusercontent.com/User1/Repo/v0.3.4/lib/utils/util.py'
        cls.invalid_github_url = 'https://github.com/User1/Repo.git'

    def test_is_authenticated_no_auth_header(self):
        """Request without 'auth' key in header should not be treated as authenticated.
        """
        self.assertFalse(lira_utils.is_authenticated({'foo': 'bar'}, 'baz'))

    def test_is_authenticated_wrong_auth_value(self):
        """Request with wrong auth value(token) in header should not be treated as authenticated.
        """
        self.assertFalse(lira_utils.is_authenticated({'auth': 'bar'}, 'foo'))

    def test_is_authenticated_valid(self):
        """Request with valid auth and token information should be treated as authenticated.
        """
        self.assertTrue(lira_utils.is_authenticated({'auth': 'bar'}, 'bar'))

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
        uuid, version, subscription_id = lira_utils.extract_uuid_version_subscription_id(body)
        self.assertEqual(uuid, 'foo')
        self.assertEqual(version, 'bar')
        self.assertEqual(subscription_id, "85test0j-u6y6-uuuu-a90a-kk8")

    def test_compose_inputs(self):
        """Test if compose_inputs can correctly create Cromwell inputs file containing bundle uuid and version"""
        inputs = lira_utils.compose_inputs('foo', 'bar', 'baz', 'asdf')
        self.assertEqual(inputs['foo.bundle_uuid'], 'bar')
        self.assertEqual(inputs['foo.bundle_version'], 'baz')
        self.assertEqual(inputs['foo.runtime_environment'], 'asdf')

    def test_parse_github_resource_url(self):
        """Test if parse_github_resource_url can correctly parse Github resource urls."""
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).repo, 'Repo')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).owner, 'Organization')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).version, 'master')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).file, 'util.py')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).path, 'lib/utils/util.py')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).repo, 'Repo')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).owner, 'User1')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).version, 'v0.3.4')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).file, 'util.py')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).path, 'lib/utils/util.py')
        self.assertRaises(ValueError, lira_utils.parse_github_resource_url, self.invalid_github_url)

    def test_merge_two_dicts(self):
        """Test if merge_two_dicts can correctly merge two dicts."""
        self.assertEqual(lira_utils.merge_two_dicts({'a': 1}, {'b': 2}), {'a': 1, 'b': 2})


if __name__ == '__main__':
    unittest.main()
