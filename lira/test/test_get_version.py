#!/usr/bin/env python
import cromwell_tools
import json
import os
import unittest
try:
    # if python3
    import unittest.mock as mock
except ImportError:
    # if python2
    import mock


class TestGetVersion(unittest.TestCase):
    @classmethod
    def setUp(cls):
        """load the config file. """
        # Change to test directory, as tests may have been invoked from another dir
        dir = os.path.abspath(os.path.dirname(__file__))
        os.chdir(dir)
        env = mock.patch.dict('os.environ', {'lira_config': 'data/config.json'})
        with env:
            # Import lira here to get the config from os.environ correctly
            from lira import lira as test_lira

            test_lira.app.testing = True
            cls.client = test_lira.app.app.test_client()
            test_lira.app.app.launch_time = '2018-01-01 00:59:59 +00:00'

    def test_get_version_can_fetch_correct_workflow_info(self):
        response = self.client.get('/version')
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_response.get('workflow_info').get('AdapterSs2RsemSingleSample').get('version'), 'smartseq2_v1.0.0')
        self.assertEqual(json_response.get('workflow_info').get('AdapterSs2RsemSingleSample').get('subscription_id'), 'dd17bb03-7634-47a4-9fd3-a55580ac3b1c')
        self.assertEqual(json_response.get('workflow_info').get('Adapter10xCount').get('version'), '10x_v0.1.0')
        self.assertEqual(json_response.get('workflow_info').get('Adapter10xCount').get('subscription_id'), '3e3e176b-629f-46ea-b01d-e36bd650dc54')

    def test_get_version_can_fetch_correct_settings_info(self):
        response = self.client.get('/version')
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_response.get('settings_info').get('launch_time'), '2018-01-01 00:59:59 +00:00')
        self.assertEqual(json_response.get('settings_info').get('run_mode'), 'live_run')
        self.assertEqual(json_response.get('settings_info').get('ingest_url'), 'https://api.ingest.dev.data.humancellatlas.org/')
        self.assertEqual(json_response.get('settings_info').get('data_store_url'), 'https://dss.dev.data.humancellatlas.org/v1')
        self.assertEqual(json_response.get('settings_info').get('cromwell_url'), 'https://cromwell.mint-dev.broadinstitute.org/api/workflows/v1')
        self.assertEqual(json_response.get('settings_info').get('max_cromwell_retries'), 0)
        self.assertEqual(json.dumps(json_response.get('settings_info').get('use_caas')), 'false')

    def test_get_version_can_fetch_correct_version_info(self):
        response = self.client.get('/version')
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_response.get('version_info').get('lira_version'), 'v0.1.0')
        self.assertEqual(json_response.get('version_info').get('cromwell_tools_version'), cromwell_tools.__version__)
        self.assertEqual(json_response.get('version_info').get('submit_wdl_version'), 'v0.1.5')
