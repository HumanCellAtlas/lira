#!/usr/bin/env python
import unittest
import flask
import requests_mock
import requests
import json
import os
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import email.utils
from requests_http_signature import HTTPSignatureAuth
from lira import lira_utils, lira_config


class NoDateHTTPSignatureAuth(HTTPSignatureAuth):
    def add_date(self, request, timestamp=None):
        pass

    def add_digest(self, request):
        pass

    @classmethod
    def get_string_to_sign(self, request, headers):
        headers.remove('date')
        return HTTPSignatureAuth.get_string_to_sign(request, headers)


class NoDigestHTTPSignatureAuth(HTTPSignatureAuth):
    def add_digest(self, request):
        pass


class NoDateNoDigestHTTPSignatureAuth(HTTPSignatureAuth):
    def add_date(self, request, timestamp=None):
        pass

    def add_digest(self, request):
        pass

    @classmethod
    def get_string_to_sign(self, request, headers):
        headers.remove('date')
        return HTTPSignatureAuth.get_string_to_sign(request, headers)


class TestUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid_github_url = (
            'https://github.com/HumanCellAtlas/adapter-pipelines/blob/master/pipelines/'
            'ss2_single_sample/static_inputs.json'
        )
        cls.valid_github_raw_url = 'https://github.com/HumanCellAtlas/skylab/blob/v0.3.0/pipelines/smartseq2_single_sample/ss2_single_sample.wdl'
        cls.invalid_github_url = (
            'https://github.com/HumanCellAtlas/adapter-pipelines.git'
        )
        cls.workflow_name = 'SmartSeq2Workflow'
        cls.workflow_version = 'v0.0.1'
        cls.bundle_uuid = 'foo-bar-id'
        cls.bundle_version = '2018-01-01T10:10:10.384Z'
        cls.extra_label_1 = {'Comment1': 'Test1'}
        cls.extra_label_2 = {'Comment2': 'Test2'}
        cls.extra_label_3 = {'Comment3': 'Test3'}
        cls.invalid_extra_label = None
        cls.invalid_long_label = {'Long': 's' * 300}
        cls.list_label = {'list_label': ['test']}
        cls.invalid_list_label = {'list_label': ['test', 'test2']}
        cls.attachments = {
            'submitter_id': None,
            'sample_id': ['b1829a9d-6678-493b-bf98-01520f9bad52'],
            'project_shortname': 'Glioblastoma_medium_1000_cells',
        }
        # Change to test directory, as tests may have been invoked from another dir
        dir = os.path.abspath(os.path.dirname(__file__))
        os.chdir(dir)
        os.environ['caas_key'] = '/test/caas_key.json'
        with open('data/config.json') as f:
            cls.correct_test_config = json.load(f)
        with open('data/options.json') as f:
            cls.options_json = f.read()
        with open('data/options_with_runtime_params.json') as f:
            cls.options_with_runtime_json = f.read()

    def test_is_authenticated_query_param_no_auth_header(self):
        """Request without 'auth' key in header should not be treated as authenticated.
        """
        self.assertFalse(
            lira_utils._is_authenticated_query_param({'foo': 'bar'}, 'baz')
        )

    def test_is_authenticated_query_param_wrong_auth_value(self):
        """Request with wrong auth value(token) in header should not be treated as authenticated.
        """
        self.assertFalse(
            lira_utils._is_authenticated_query_param({'auth': 'bar'}, 'foo')
        )

    def test_is_authenticated_query_param_valid(self):
        """Request with valid auth and token information should be treated as authenticated.
        """
        self.assertTrue(
            lira_utils._is_authenticated_query_param({'auth': 'bar'}, 'bar')
        )

    def test_is_authenticated_hmac_no_auth_header(self):
        """Test that request with no auth header is rejected"""
        app = flask.Flask(__name__)
        with app.test_client() as c:
            c.post('/notifications', headers={'foo': 'bar'}, data={'foo': 'bar'})
            self.assertFalse(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key')
            )

    def test_is_authenticated_hmac_empty_auth_header(self):
        """Test that request with empty auth header is rejected"""
        app = flask.Flask(__name__)
        with app.test_client() as c:
            c.post('/notifications', headers={'Authorization': ''}, data={'foo': 'bar'})
            self.assertFalse(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key')
            )

    def test_is_authenticated_hmac_stub_auth_header(self):
        """Test that request with stub auth header is rejected"""
        app = flask.Flask(__name__)
        with app.test_client() as c:
            c.post(
                '/notifications',
                headers={'Authorization': 'Signature '},
                data={'foo': 'bar'},
            )
            self.assertFalse(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key')
            )

    def test_is_authenticated_hmac_bad_signature(self):
        """Test that request with bad hmac signature is rejected"""

        def matcher(request):
            response = requests.Response()
            d = {x: request.headers[x] for x in request.headers}
            print(d)
            response._content = json.dumps(d).encode('utf-8')
            return response

        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.add_matcher(matcher)

        response = session.post(
            'mock://notifications',
            json={'foo': 'bar'},
            auth=HTTPSignatureAuth(key_id='foo_id', key=b'foo_key'),
        )
        app = flask.Flask(__name__)
        with app.test_client() as c:
            headers = response.json()
            auth_header = headers.get('Authorization')
            new_auth_header = auth_header[: auth_header.find('signature')]
            new_auth_header += 'signature=blah'
            headers['Authorization'] = new_auth_header
            c.post(
                '/notifications',
                headers=headers,
                data=json.dumps({'foo': 'bar'}).encode('utf-8'),
            )
            self.assertFalse(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key')
            )

    def test_is_authenticated_hmac_old_date_rejected(self):
        """Test that request with old date is rejected"""

        def matcher(request):
            response = requests.Response()
            d = {x: request.headers[x] for x in request.headers}
            response._content = json.dumps(d).encode('utf-8')
            return response

        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.add_matcher(matcher)

        raw_headers = {
            'Date': email.utils.format_datetime(
                datetime.now(tz=timezone.utc) - timedelta(seconds=100), usegmt=True
            )
        }
        response = session.post(
            'mock://notifications',
            json={'foo': 'bar'},
            headers=raw_headers,
            auth=HTTPSignatureAuth(key_id='foo_id', key=b'foo_key'),
        )

        app = flask.Flask(__name__)
        with app.test_client() as c:
            headers = response.json()
            c.post(
                '/notifications',
                headers=headers,
                data=json.dumps({'foo': 'bar'}).encode('utf-8'),
            )
            self.assertFalse(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key', 60)
            )

    def test_is_authenticated_hmac_old_date_accepted_if_timeout_zero(self):
        """Test that request with old date is accepted if stale notification timeout is zero"""

        def matcher(request):
            response = requests.Response()
            d = {x: request.headers[x] for x in request.headers}
            response._content = json.dumps(d).encode('utf-8')
            return response

        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.add_matcher(matcher)

        raw_headers = {
            'Date': email.utils.format_datetime(
                datetime.now(tz=timezone.utc) - timedelta(seconds=100), usegmt=True
            )
        }
        response = session.post(
            'mock://notifications',
            json={'foo': 'bar'},
            headers=raw_headers,
            auth=HTTPSignatureAuth(key_id='foo_id', key=b'foo_key'),
        )

        app = flask.Flask(__name__)
        with app.test_client() as c:
            headers = response.json()
            c.post(
                '/notifications',
                headers=headers,
                data=json.dumps({'foo': 'bar'}).encode('utf-8'),
            )
            self.assertTrue(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key', 0)
            )

    def test_is_authenticated_hmac_no_date(self):
        """Test that request with valid signature but no date is rejected"""

        def matcher(request):
            response = requests.Response()
            d = {x: request.headers[x] for x in request.headers}
            response._content = json.dumps(d).encode('utf-8')
            return response

        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.add_matcher(matcher)

        response = session.post(
            'mock://notifications',
            json={'foo': 'bar'},
            auth=NoDateHTTPSignatureAuth(key_id='foo_id', key=b'foo_key'),
        )

        app = flask.Flask(__name__)
        with app.test_client() as c:
            c.post(
                '/notifications',
                headers=response.json(),
                data=json.dumps({'foo': 'bar'}).encode('utf-8'),
            )
            self.assertFalse(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key')
            )

    def test_is_authenticated_hmac_no_digest(self):
        """Test that request with valid signature but no digest is rejected"""

        def matcher(request):
            response = requests.Response()
            d = {x: request.headers[x] for x in request.headers}
            response._content = json.dumps(d).encode('utf-8')
            return response

        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.add_matcher(matcher)

        response = session.post(
            'mock://notifications',
            json={'foo': 'bar'},
            auth=NoDigestHTTPSignatureAuth(key_id='foo_id', key=b'foo_key'),
        )

        app = flask.Flask(__name__)
        with app.test_client() as c:
            c.post(
                '/notifications',
                headers=response.json(),
                data=json.dumps({'foo': 'bar'}).encode('utf-8'),
            )
            self.assertFalse(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key')
            )

    def test_is_authenticated_hmac_bad_digest(self):
        """Test that request with valid signature but mismatching digest is rejected"""

        def matcher(request):
            response = requests.Response()
            d = {x: request.headers[x] for x in request.headers}
            response._content = json.dumps(d).encode('utf-8')
            return response

        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.add_matcher(matcher)

        response = session.post(
            'mock://notifications',
            json={'foo': 'bar'},
            auth=HTTPSignatureAuth(key_id='foo_id', key=b'foo_key'),
        )

        app = flask.Flask(__name__)
        with app.test_client() as c:
            headers = response.json()
            headers['Digest'] = 'blah'
            c.post(
                '/notifications',
                headers=headers,
                data=json.dumps({'foo': 'bar'}).encode('utf-8'),
            )
            self.assertFalse(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key')
            )

    def test_is_authenticated_hmac_no_date_no_digest(self):
        """Test that request with valid signature but no date and no digest is rejected"""

        def matcher(request):
            response = requests.Response()
            d = {x: request.headers[x] for x in request.headers}
            response._content = json.dumps(d).encode('utf-8')
            return response

        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.add_matcher(matcher)

        response = session.post(
            'mock://notifications',
            json={'foo': 'bar'},
            auth=NoDateNoDigestHTTPSignatureAuth(key_id='foo_id', key=b'foo_key'),
        )

        app = flask.Flask(__name__)
        with app.test_client() as c:
            c.post(
                '/notifications',
                headers=response.json(),
                data=json.dumps({'foo': 'bar'}).encode('utf-8'),
            )
            self.assertFalse(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key')
            )

    def test_is_authenticated_hmac(self):
        """Test that request with correct auth header is accepted"""

        def matcher(request):
            response = requests.Response()
            d = {x: request.headers[x] for x in request.headers}
            response._content = json.dumps(d).encode('utf-8')
            return response

        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.add_matcher(matcher)

        response = session.post(
            'mock://notifications',
            json={'foo': 'bar'},
            auth=HTTPSignatureAuth(key_id='foo_id', key=b'foo_key'),
        )
        app = flask.Flask(__name__)
        with app.test_client() as c:
            c.post(
                '/notifications',
                headers=response.json(),
                data=json.dumps({'foo': 'bar'}).encode('utf-8'),
            )
            self.assertTrue(
                lira_utils._is_authenticated_hmac(flask.request, b'foo_key')
            )

    def test_extract_uuid_version_subscription_id(self):
        """Test if extract_uuid_version_subscription_id can correctly extract uuid, version
         and subscription from body content."""
        body = {
            'subscription_id': "85test0j-u6y6-uuuu-a90a-kk8",
            'match': {'bundle_uuid': 'foo', 'bundle_version': 'bar'},
        }
        uuid, version, subscription_id = lira_utils.extract_uuid_version_subscription_id(
            body
        )
        self.assertEqual(uuid, 'foo')
        self.assertEqual(version, 'bar')
        self.assertEqual(subscription_id, "85test0j-u6y6-uuuu-a90a-kk8")

    def test_compose_inputs(self):
        """Test if compose_inputs can correctly create Cromwell inputs file containing bundle uuid and version"""
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        inputs = lira_utils.compose_inputs('foo', 'bar', 'baz', config)
        self.assertEqual(inputs['foo.bundle_uuid'], 'bar')
        self.assertEqual(inputs['foo.bundle_version'], 'baz')
        self.assertEqual(inputs['foo.runtime_environment'], 'dev')
        self.assertEqual(
            inputs['foo.dss_url'], 'https://dss.dev.data.humancellatlas.org/v1'
        )
        self.assertEqual(
            inputs['foo.submit_url'], 'https://api.ingest.dev.data.humancellatlas.org/'
        )
        self.assertEqual(
            inputs['foo.cromwell_url'],
            'https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1',
        )

    def test_compose_caas_options(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['caas_key'] = 'data/fake_caas_key.json'
        test_config['gcs_root'] = 'fake_gcs_root'
        test_config['google_project'] = 'fake_google_project'
        test_config['user_service_account_json'] = 'fake_caas_key'
        config = lira_config.LiraConfig(test_config)
        options = lira_utils.compose_caas_options(self.options_json, config)
        self.assertEqual(options['jes_gcs_root'], 'fake_gcs_root')
        self.assertEqual(options['google_project'], 'fake_google_project')
        with open('data/fake_caas_key.json') as f:
            fake_caas_key = f.read()
            fake_caas_key_json = json.loads(fake_caas_key)
        self.assertEqual(options['user_service_account_json'], fake_caas_key)
        self.assertEqual(
            options['google_compute_service_account'],
            fake_caas_key_json['client_email'],
        )

    def test_max_retries_uses_value_set_in_options_file(self):
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        options_from_file = json.loads(self.options_with_runtime_json)
        expected_max_retries = options_from_file['default_runtime_attributes'][
            'maxRetries'
        ]
        options = lira_utils.compose_config_options(
            self.options_with_runtime_json, config
        )
        max_retries = json.loads(options)['default_runtime_attributes']['maxRetries']
        self.assertEqual(max_retries, expected_max_retries)

    def test_max_retries_uses_value_from_lira_config_if_not_set_in_options(self):
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        expected_max_retries = config.get('max_cromwell_retries')
        options_from_file = json.loads(self.options_json)
        runtime_parameters = options_from_file.get('default_runtime_attributes', {})
        self.assertIsNone(runtime_parameters.get('maxRetries'))
        options = lira_utils.compose_config_options(self.options_json, config)
        max_retries = json.loads(options)['default_runtime_attributes']['maxRetries']
        self.assertEqual(max_retries, expected_max_retries)

    def test_parse_github_resource_url(self):
        """Test if parse_github_resource_url can correctly parse Github resource urls."""
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_url).repo,
            'adapter-pipelines',
        )
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_url).owner,
            'HumanCellAtlas',
        )
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_url).version,
            'master',
        )
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_url).file,
            'static_inputs.json',
        )
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_url).path,
            'pipelines/ss2_single_sample/static_inputs.json',
        )
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_raw_url).repo,
            'skylab',
        )
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_raw_url).owner,
            'HumanCellAtlas',
        )
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_raw_url).version,
            'v0.3.0',
        )
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_raw_url).file,
            'ss2_single_sample.wdl',
        )
        self.assertEqual(
            lira_utils.parse_github_resource_url(self.valid_github_raw_url).path,
            'pipelines/smartseq2_single_sample/ss2_single_sample.wdl',
        )
        self.assertRaises(
            ValueError, lira_utils.parse_github_resource_url, self.invalid_github_url
        )

    def test_compose_labels_no_extra_labels(self):
        """Test if compose_labels can correctly compose labels without extra labels."""
        expected_labels = {
            'workflow-name': 'SmartSeq2Workflow',
            'workflow-version': 'v0.0.1',
            'bundle-uuid': 'foo-bar-id',
            'bundle-version': '2018-01-01T10:10:10.384Z',
        }
        self.assertEqual(
            lira_utils.compose_labels(
                self.workflow_name,
                self.workflow_version,
                self.bundle_uuid,
                self.bundle_version,
            ),
            expected_labels,
        )

    def test_compose_labels_with_one_extra_label(self):
        """Test if compose_labels can correctly compose labels with one extra label."""
        expected_labels = {
            'workflow-name': 'SmartSeq2Workflow',
            'workflow-version': 'v0.0.1',
            'bundle-uuid': 'foo-bar-id',
            'bundle-version': '2018-01-01T10:10:10.384Z',
            'Comment1': 'Test1',
        }
        self.assertEqual(
            lira_utils.compose_labels(
                self.workflow_name,
                self.workflow_version,
                self.bundle_uuid,
                self.bundle_version,
                self.extra_label_1,
            ),
            expected_labels,
        )

    def test_compose_labels_with_one_extra_invalid_label(self):
        """Test if compose_labels can correctly compose labels with one invalid long label."""
        expected_labels = {
            'workflow-name': 'SmartSeq2Workflow',
            'workflow-version': 'v0.0.1',
            'bundle-uuid': 'foo-bar-id',
            'bundle-version': '2018-01-01T10:10:10.384Z',
            'Long': 's' * 255,
        }
        self.assertEqual(
            lira_utils.compose_labels(
                self.workflow_name,
                self.workflow_version,
                self.bundle_uuid,
                self.bundle_version,
                self.invalid_long_label,
            ),
            expected_labels,
        )

    def test_compose_labels_with_one_extra_list_label(self):
        """Test if compose_labels can correctly compose labels with one list as a label."""
        expected_labels = {
            'workflow-name': 'SmartSeq2Workflow',
            'workflow-version': 'v0.0.1',
            'bundle-uuid': 'foo-bar-id',
            'bundle-version': '2018-01-01T10:10:10.384Z',
            'list_label': 'test',
        }
        self.assertEqual(
            lira_utils.compose_labels(
                self.workflow_name,
                self.workflow_version,
                self.bundle_uuid,
                self.bundle_version,
                self.list_label,
            ),
            expected_labels,
        )

    def test_compose_labels_with_invalid_list_label_raises_error(self):
        """Test if compose_labels can correctly compose labels with one list as a label."""
        self.assertRaises(
            ValueError,
            lira_utils.compose_labels,
            self.workflow_name,
            self.workflow_version,
            self.bundle_uuid,
            self.bundle_version,
            self.invalid_list_label,
        )

    def test_compose_labels_with_multiple_extra_labels(self):
        """Test if compose_labels can correctly compose labels with multiple extra labels."""
        expected_labels = {
            'workflow-name': 'SmartSeq2Workflow',
            'workflow-version': 'v0.0.1',
            'bundle-uuid': 'foo-bar-id',
            'bundle-version': '2018-01-01T10:10:10.384Z',
            'Comment1': 'Test1',
            'Comment2': 'Test2',
            'Comment3': 'Test3',
        }
        self.assertEqual(
            lira_utils.compose_labels(
                self.workflow_name,
                self.workflow_version,
                self.bundle_uuid,
                self.bundle_version,
                self.extra_label_1,
                self.extra_label_2,
                self.extra_label_3,
                self.invalid_extra_label,
            ),
            expected_labels,
        )

    def test_compose_labels_with_labels_and_attachments(self):
        """Test if compose_labels can correctly compose labels with extra labels and attachments."""
        expected_labels = {
            'workflow-name': 'SmartSeq2Workflow',
            'workflow-version': 'v0.0.1',
            'bundle-uuid': 'foo-bar-id',
            'bundle-version': '2018-01-01T10:10:10.384Z',
            'Comment1': 'Test1',
            'Comment2': 'Test2',
            'Comment3': 'Test3',
            'submitter_id': 'None',
            'sample_id': 'b1829a9d-6678-493b-bf98-01520f9bad52',
            'project_shortname': 'Glioblastoma_medium_1000_cells',
        }
        self.assertEqual(
            lira_utils.compose_labels(
                self.workflow_name,
                self.workflow_version,
                self.bundle_uuid,
                self.bundle_version,
                self.extra_label_1,
                self.extra_label_2,
                self.extra_label_3,
                self.invalid_extra_label,
                self.attachments,
            ),
            expected_labels,
        )


if __name__ == '__main__':
    unittest.main()
