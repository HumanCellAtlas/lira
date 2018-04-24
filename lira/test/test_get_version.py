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
import logging


class TestGetVersion(unittest.TestCase):
    @classmethod
    def setUp(cls):
        """load the config file. """
        # Change to test directory, as tests may have been invoked from another dir
        dir = os.path.abspath(os.path.dirname(__file__))
        os.chdir(dir)
        env = mock.patch.dict('os.environ', {'listener_config': 'data/config.json'})
        with env:
            # Import lira here to get the config from os.environ correctly
            from lira import lira

            lira.app.testing = True
            cls.client = lira.app.app.test_client()
            lira.app.app.config_name = 'lira-config-2018-01-01-00-59'
            lira.app.app.launch_time = '2018-01-01 00:59:59 +00:00'

    def test_get_version(self):
        response = self.client.get('/version')
        json_response = json.loads(response.data.decode('utf-8'))
        logging.info(str(response.status_code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_response.get('config_version'), 'lira-config-2018-01-01-00-59')
        self.assertEqual(json_response.get('launch_time'), '2018-01-01 00:59:59 +00:00')
        self.assertEqual(json_response.get('Lira_version'), 'v0.1.0')
        self.assertEqual(json_response.get('Cromwell_tools_version'), cromwell_tools.__version__)
        self.assertEqual(json_response.get('submit_wdl_version'), 'v0.1.5')
        self.assertEqual(json_response.get('run_mode'), 'live_run')
        self.assertEqual(json_response.get('workflow_info').get('AdapterSs2RsemSingleSample').get('version'), 'smartseq2_v0.2.0')
        self.assertEqual(json_response.get('workflow_info').get('AdapterSs2RsemSingleSample').get('subscription_id'), 'dd17bb03-7634-47a4-9fd3-a55580ac3b1c')
        self.assertEqual(json_response.get('workflow_info').get('Adapter10xCount').get('version'), '10x_v0.1.0')
        self.assertEqual(json_response.get('workflow_info').get('Adapter10xCount').get('subscription_id'), '3e3e176b-629f-46ea-b01d-e36bd650dc54')
