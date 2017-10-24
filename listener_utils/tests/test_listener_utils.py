#!/usr/bin/env python
import json
import listener_utils as utils
import os
import io
import requests
import requests_mock
from six.moves import http_client
import sys
import unittest
try:
    # if python3
    import unittest.mock as mock
except ImportError:
    # if python2
    import mock

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, pkg_root)


def _make_credentials():
    import google.auth.credentials
    return mock.Mock(spec=google.auth.credentials.Credentials)


def _make_response(status=http_client.OK, content=b'', headers=None):  # this is python3 style
    headers = headers or {}
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
    @classmethod
    def setUpClass(cls):
        cls.PROJECT = 'PROJECT'
        cls.CREDENTIALS = _make_credentials()
        cls.BUCKET_NAME = 'BUCKET_NAME'
        cls.client = mock.Mock(project=cls.PROJECT, credentials=cls.CREDENTIALS)
        cls.bucket = cls.client.bucket(cls.BUCKET_NAME)
        cls.blob_name = 'test_blob'
        cls.blob = cls.bucket.blob(cls.blob_name)

    def test_get_filename_from_gs_link(self):
        """Test if get_filename_from_gs_link can get correct filename from google cloud storage link.
        """
        link = "gs://test_bucket_name/test_wdl_file.wdl"
        self.assertEqual(utils.get_filename_from_gs_link(link), 'test_wdl_file.wdl')

    def test_parse_bucket_blob_from_gs_link_one_slash(self):
        """Test if parse_bucket_blob_from_gs_link can correctly parse bucket name and blob name
         from a single slash google cloud storage link.
         """
        link = "gs://test_bucket_name/test_wdl_file.wdl"
        bucket_name, blob_name = utils.parse_bucket_blob_from_gs_link(link)
        self.assertEqual(bucket_name, 'test_bucket_name')
        self.assertEqual(blob_name, 'test_wdl_file.wdl')

    def test_parse_bucket_blob_from_gs_link_extra_slashes(self):
        """Test if parse_bucket_blob_from_gs_link can correctly parse bucket name and blob name
         from a slash google cloud storage link with extra slashes.
        """
        link = "gs://test_bucket_name/special/test/wdl/file.wdl"
        bucket_name, blob_name = utils.parse_bucket_blob_from_gs_link(link)
        self.assertEqual(bucket_name, 'test_bucket_name')
        self.assertEqual(blob_name, 'special/test/wdl/file.wdl')

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

    @requests_mock.mock()
    def test_start_workflow(self, mock_request):
        """This is a temporary unit test using mocks, to be replaced with an integration test later.
        """
        wdl_file = io.BytesIO(b"wdl_file")
        zip_file = io.BytesIO(b"zip_file")
        inputs_file = io.BytesIO(b"inputs_file")
        inputs_file2 = io.BytesIO(b"inputs_file2")
        options_file = io.BytesIO(b"options_file")
        green_config = type('Config', (object,), {"cromwell_url": "http://cromwell_url",
                                                  "cromwell_user": "cromwell_user",
                                                  "cromwell_password": "cromwell_password"})

        def _request_callback(request, context):
            context.status_code = 200
            context.headers['test'] = 'header'
            return {'request': {'body': "content"}}

        # Check request actions
        mock_request.post(green_config.cromwell_url, json=_request_callback)
        result = utils.start_workflow(wdl_file, zip_file, inputs_file, inputs_file2, options_file, green_config)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers.get('test'), 'header')

    def test_download_to_bytes_readable(self):
        """Test if download_to_buffer correctly download blob and store it into Bytes Buffer."""
        result = utils.download_to_buffer(self.bucket.blob(self.blob_name))
        self.assertIsInstance(result, io.BytesIO)

    def test_download_gcs_blob(self):
        """Test if download_gcs_blob can correctly create destination file on the disk."""
        gcs_client = utils.GoogleCloudStorageClient(key_location="test_key", scopes=['test_scope'])
        gcs_client.storage_client = self.client
        result = utils.download_gcs_blob(gcs_client, self.BUCKET_NAME, self.blob_name)
        self.assertIsInstance(result, io.BytesIO)

    def test_lazyproperty_initialize_late_for_gcs_client(self):
        """Test if the LazyProperty decorator can work well with GoogleCloudStorageClient class."""
        gcs_client = utils.GoogleCloudStorageClient(key_location="test_key", scopes=['test_scope'])
        self.assertIsNotNone(gcs_client)
        self.assertEqual(gcs_client.key_location, "test_key")
        self.assertEqual(gcs_client.scopes[0], "test_scope")


if __name__ == '__main__':
    unittest.main()
