#!/usr/bin/env python
import unittest
from lira import lira_utils


class TestUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.valid_github_url = 'https://github.com/HumanCellAtlas/pipeline-tools/blob/master/adapter_pipelines/' \
                               'ss2_single_sample/adapter_example_static.json'
        cls.valid_github_raw_url = 'https://github.com/HumanCellAtlas/skylab/blob/v0.3.0/pipelines/smartseq2_single_sample/ss2_single_sample.wdl'
        cls.invalid_github_url = 'https://github.com/HumanCellAtlas/pipeline-tools.git'
        cls.workflow_name = 'SmartSeq2Workflow'
        cls.workflow_version = 'v0.0.1'
        cls.bundle_uuid = 'foo-bar-id'
        cls.bundle_version = '2018-01-01T10:10:10.384Z'
        cls.extra_labels = {'Comment': 'Test'}

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
        inputs = lira_utils.compose_inputs('foo', 'bar', 'baz', 'asdf', False)
        self.assertEqual(inputs['foo.bundle_uuid'], 'bar')
        self.assertEqual(inputs['foo.bundle_version'], 'baz')
        self.assertEqual(inputs['foo.runtime_environment'], 'asdf')
        self.assertEqual(inputs['foo.use_caas'], False)

    def test_parse_github_resource_url(self):
        """Test if parse_github_resource_url can correctly parse Github resource urls."""
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).repo,
                         'pipeline-tools')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).owner,
                         'HumanCellAtlas')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).version,
                         'master')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).file,
                         'adapter_example_static.json')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_url).path,
                         'adapter_pipelines/ss2_single_sample/adapter_example_static.json')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).repo,
                         'skylab')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).owner,
                         'HumanCellAtlas')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).version,
                         'v0.3.0')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).file,
                         'ss2_single_sample.wdl')
        self.assertEqual(lira_utils.parse_github_resource_url(self.valid_github_raw_url).path,
                         'pipelines/smartseq2_single_sample/ss2_single_sample.wdl')
        self.assertRaises(ValueError, lira_utils.parse_github_resource_url, self.invalid_github_url)

    def test_compose_labels_no_extra_labels(self):
        """Test if compose_labels can correctly compose labels without extra labels."""
        expected_labels = {
            "workflow-name": 'smartseq2workflow',
            "workflow-version": 'v0-0-1',
            "bundle-uuid": 'foo-bar-id',
            "bundle-version": '2018-01-01t10-10-10-384z'
        }
        self.assertEqual(lira_utils.compose_labels(
            self.workflow_name, self.workflow_version, self.bundle_uuid, self.bundle_version), expected_labels)

    def test_compose_labels_with_extra_labels(self):
        """Test if compose_labels can correctly compose labels with extra labels."""
        expected_labels = {
            "workflow-name": 'smartseq2workflow',
            "workflow-version": 'v0-0-1',
            "bundle-uuid": 'foo-bar-id',
            "bundle-version": '2018-01-01t10-10-10-384z',
            "comment": 'test'
        }
        self.assertEqual(lira_utils.compose_labels(self.workflow_name, self.workflow_version, self.bundle_uuid,
                                                   self.bundle_version, self.extra_labels), expected_labels)


if __name__ == '__main__':
    unittest.main()
