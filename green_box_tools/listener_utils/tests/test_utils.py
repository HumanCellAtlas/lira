#!/usr/bin/env python

import os
import sys
import unittest

try:
    # if python3
    import unittest.mock as mock
    from unittest.mock import call
except ImportError:
    # if python2
    import mock
    from mock import call


import requests_mock
from six.moves import http_client
import tempfile

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, pkg_root)

from listener_utils.utils import *


def _make_credentials():
    import google.auth.credentials

    return mock.Mock(spec=google.auth.credentials.Credentials)


def _make_response(status=http_client.OK, content=b'', headers={}):  # this is python3 style
    response = requests.Response()
    response.status_code = status
    response._content = content
    response.headers = headers
    response.request = requests.Request()
    return response


def _make_json_response(data, status=http_client.OK, headers=None):
    headers = headers or {}
    headers['Content-Type'] = 'application/json'
    return _make_response(
        status=status,
        content=json.dumps(data).encode('utf-8'),
        headers=headers)


def _make_requests_session(responses):
    session = mock.create_autospec(requests.Session, instance=True)
    session.request.side_effect = responses
    return session


class TestUtils(unittest.TestCase):

    @staticmethod
    def _get_target_class():
        from google.cloud.storage.client import Client

        return Client

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_get_filename_from_gs_link(self):
        link = "gs://test_bucket_name/test_wdl_file.wdl"
        self.assertEqual(get_filename_from_gs_link(link), 'test_wdl_file.wdl')

    def test_parse_bucket_blob_from_gs_link_normal_link(self):
        link = "gs://test_bucket_name/test_wdl_file.wdl"
        bucket_name, blob_name = parse_bucket_blob_from_gs_link(link)
        self.assertEqual(bucket_name, 'test_bucket_name')
        self.assertEqual(blob_name, 'test_wdl_file.wdl')

    def test_parse_bucket_blob_from_gs_link_special_link(self):
        link = "gs://test_bucket_name/special/test/wdl/file.wdl"
        bucket_name, blob_name = parse_bucket_blob_from_gs_link(link)
        self.assertEqual(bucket_name, 'test_bucket_name')
        self.assertEqual(blob_name, 'special/test/wdl/file.wdl')

    def test_is_authenticated_no_auth_header(self):
        self.assertFalse(is_authenticated({'foo': 'bar'}, 'baz'))

    def test_is_authenticated_wrong_auth_value(self):
        self.assertFalse(is_authenticated({'auth': 'bar'}, 'foo'))

    def test_is_authenticated_valid(self):
        self.assertTrue(is_authenticated({'auth': 'bar'}, 'bar'))

    def test_extract_uuid_version_subscription_id(self):
        body = {
            'subscription_id': 222,
            'match': {
                'bundle_uuid': 'foo',
                'bundle_version': 'bar'
            }
        }
        uuid, version, subscription_id = extract_uuid_version_subscription_id(body)
        self.assertEqual(uuid, 'foo')
        self.assertEqual(version, 'bar')
        self.assertEqual(subscription_id, 222)

    def test_compose_inputs(self):
        inputs = compose_inputs('foo', 'bar', 'baz')
        self.assertEqual(inputs['foo.bundle_uuid'], 'bar')
        self.assertEqual(inputs['foo.bundle_version'], 'baz')

    @mock.patch("listener_utils.utils.open", create=True)
    @requests_mock.mock()
    def test_start_workflow(self, mock_open, mock_request):
        """NOTE: This is just a workaround unittest, Integration test should be imported to further test!"""
        wdl_file = "wdl_file"
        zip_file = "zip_file"
        inputs_file = "inputs_file"
        inputs_file2 = "inputs_file2"
        options_file = "options_file"
        green_config = type('Config', (object,), {"cromwell_url": "http://cromwell_url",
                                                  "cromwell_user": "cromwell_user",
                                                  "cromwell_password": "cromwell_password"})

        mock_open.side_effect = [
            mock.mock_open(read_data="wdl_file").return_value,
            mock.mock_open(read_data="zip_file").return_value,
            mock.mock_open(read_data="inputs_file").return_value,
            mock.mock_open(read_data="inputs_file2").return_value,
            mock.mock_open(read_data="options_file").return_value
        ]

        file = {
            'wdlSource': "wdl_file",
            'workflowInputs': "inputs_file",
            'workflowInputs_2': "inputs_file2",
            'wdlDependencies': "zip_file",
            'workflowOptions': "options_file"
        }

        def _request_callback(request, context):
            context.status_code = 200
            context.headers['test'] = 'header'
            return {'request': {'body': "content"}}

        # Check request actions
        mock_request.post(green_config.cromwell_url, json=_request_callback)
        result = start_workflow(wdl_file, zip_file, inputs_file, inputs_file2, options_file, green_config)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers.get('test'), 'header')

        # Check file open actions
        calls = [call(wdl_file, 'rb'), call(zip_file, 'rb'), call(inputs_file, 'rb'),
                 call(inputs_file2, 'rb'), call(options_file, 'rb')]
        mock_open.assert_has_calls(calls)

    def test_download_gcs_blob_check_client(self):
        from google.cloud.storage.bucket import Bucket

        PROJECT = 'PROJECT'
        CREDENTIALS = _make_credentials()
        BUCKET_NAME = 'BUCKET_NAME'

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        bucket = client.bucket(BUCKET_NAME)
        self.assertIsInstance(bucket, Bucket)
        self.assertIs(bucket.client, client)
        self.assertEqual(bucket.name, BUCKET_NAME)

    def test_download_gcs_blob_hit(self):
        PROJECT = 'PROJECT'
        CREDENTIALS = _make_credentials()
        BUCKET_NAME = 'BUCKET_NAME'

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        bucket = client.bucket(BUCKET_NAME)
        blob_name = bucket.blob('test_blob')

        with tempfile.NamedTemporaryFile() as dest_file:
            download_gcs_blob(
                client,
                'BUCKET_NAME',
                blob_name,
                dest_file.name
            )
            assert os.path.exists(dest_file.name)  # NOTE: this is just a workaround, wait for integration test!

    def test_lazyproperty_initialize_late_with_gcs_client(self):
        gcs_client = GoogleCloudStorageClient(key_location="test_key", scopes=['test_scope'])
        self.assertIsNotNone(gcs_client)
        self.assertEqual(gcs_client.key_location, "test_key")
        self.assertEqual(gcs_client.scopes[0], "test_scope")


if __name__ == '__main__':
    unittest.main()
