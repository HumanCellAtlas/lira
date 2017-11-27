#!/usr/bin/env python
import unittest
from lira import lira_utils
import zipfile

class TestUtils(unittest.TestCase):

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
        self.assertEquals(inputs['foo.runtime_environment'], 'asdf')

    def test_download_to_map(self):
        """Test download_to_map with local files to ensure it builds the map of paths to contents correctly"""
        urls = ['data/a.txt', 'data/b.txt']
        urls_to_content = lira_utils.download_to_map(urls)
        self.assertIn('data/a.txt', urls_to_content)
        self.assertIn('data/b.txt', urls_to_content)
        self.assertEqual(urls_to_content['data/a.txt'], 'aaa\n')
        self.assertEqual(urls_to_content['data/b.txt'], 'bbb\n')

    def test_make_zip_in_memory(self):
        """Test make_zip_in_memory produces an in-memory zip file with the expected contents"""
        urls_to_content = {
            'data/a.txt': 'aaa\n',
            'data/b.txt': 'bbb\n'
        }
        bytes_buf = lira_utils.make_zip_in_memory(urls_to_content)
        with zipfile.ZipFile(bytes_buf, 'r') as zf:
            with zf.open('a.txt') as f1:
                f1_contents = f1.read()
            with zf.open('b.txt') as f2:
                f2_contents = f2.read()
        self.assertEqual(f1_contents, 'aaa\n')
        self.assertEqual(f2_contents, 'bbb\n')

if __name__ == '__main__':
    unittest.main()
