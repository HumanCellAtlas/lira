#!/usr/bin/env python
import json
import os
import requests_mock
import unittest
from lira import lira_config
from lira.lira_utils import create_prepare_submission_function

try:
    from functools import lru_cache

    cache_available = True
except ImportError:
    cache_available = False


class TestNotifications(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """load the config file"""
        # Change to test directory, as tests may have been invoked from another dir
        dir = os.path.abspath(os.path.dirname(__file__))
        os.chdir(dir)
        with open('data/config.json', 'r') as f:
            raw_config = json.load(f)
        cls.test_config = lira_config.LiraConfig(raw_config)
        cls.wdl_configs = cls.test_config.wdls
        cls.tenx_config = cls.wdl_configs[0]
        cls.ss2_config = cls.wdl_configs[1]
        cls.submit_wdl = cls.test_config.submit_wdl

    def set_up_mock(self, test_config, mock_request):
        mock_request.get(test_config.submit_wdl, text=test_config.submit_wdl)
        wdl_configs = test_config.wdls
        for wc in wdl_configs:
            mock_request.get(wc.wdl_link, text=wc.wdl_link)
            mock_request.get(wc.wdl_static_inputs_link, text=wc.wdl_static_inputs_link)
            mock_request.get(wc.options_link, text=wc.options_link)
            for url in wc.analysis_wdls:
                mock_request.get(url, text=url)

    @requests_mock.mock()
    def test_first_call_writes_to_cache(self, mock_request):
        self.set_up_mock(self.test_config, mock_request)
        prepare_submission = create_prepare_submission_function(True)
        prepare_submission(self.ss2_config, self.submit_wdl)
        info = prepare_submission.cache_info()
        if cache_available:
            self.assertEqual([info.hits, info.misses, info.currsize], [0, 1, 1])
        else:
            self.assertIsNotNone(info)

    @requests_mock.mock()
    def test_unique_calls_write_to_cache(self, mock_request):
        self.set_up_mock(self.test_config, mock_request)
        prepare_submission = create_prepare_submission_function(True)
        prepare_submission(self.ss2_config, self.submit_wdl)
        prepare_submission(self.tenx_config, self.submit_wdl)
        info = prepare_submission.cache_info()
        if cache_available:
            self.assertEqual([info.hits, info.misses, info.currsize], [0, 2, 2])
        else:
            self.assertIsNotNone(info)

    @requests_mock.mock()
    def test_repeated_calls_hit_cache(self, mock_request):
        self.set_up_mock(self.test_config, mock_request)
        prepare_submission = create_prepare_submission_function(True)
        prepare_submission(self.ss2_config, self.submit_wdl)
        prepare_submission(self.ss2_config, self.submit_wdl)
        prepare_submission(self.ss2_config, self.submit_wdl)
        info = prepare_submission.cache_info()
        if cache_available:
            self.assertEqual([info.hits, info.misses, info.currsize], [2, 1, 1])
        else:
            self.assertIsNotNone(info)

    @requests_mock.mock()
    def test_one_repeat_one_new_touches_cache_correctly(self, mock_request):
        self.set_up_mock(self.test_config, mock_request)
        prepare_submission = create_prepare_submission_function(True)
        prepare_submission(self.ss2_config, self.submit_wdl)
        prepare_submission(self.ss2_config, self.submit_wdl)
        prepare_submission(self.tenx_config, self.submit_wdl)
        info = prepare_submission.cache_info()
        if cache_available:
            self.assertEqual([info.hits, info.misses, info.currsize], [1, 2, 2])
        else:
            self.assertIsNotNone(info)

    @requests_mock.mock()
    def test_two_unique_then_repeat_touches_cache_correctly(self, mock_request):
        self.set_up_mock(self.test_config, mock_request)
        prepare_submission = create_prepare_submission_function(True)
        prepare_submission(self.ss2_config, self.submit_wdl)
        prepare_submission(self.tenx_config, self.submit_wdl)
        prepare_submission(self.ss2_config, self.submit_wdl)
        info = prepare_submission.cache_info()
        if cache_available:
            self.assertEqual([info.hits, info.misses, info.currsize], [1, 2, 2])
        else:
            self.assertIsNotNone(info)

    @requests_mock.mock()
    def test_prepare_submission_returns_correct_object(self, mock_request):
        self.set_up_mock(self.test_config, mock_request)
        prepare_submission = create_prepare_submission_function(True)
        s1 = prepare_submission(self.ss2_config, self.submit_wdl)
        self.assertIn(b'smart_seq2/adapter.wdl', s1.wdl_file)
        s2 = prepare_submission(self.tenx_config, self.submit_wdl)
        self.assertIn(b'10x/adapter.wdl', s2.wdl_file)
        s3 = prepare_submission(self.ss2_config, self.submit_wdl)
        self.assertIn(b'smart_seq2/adapter.wdl', s3.wdl_file)
        s4 = prepare_submission(self.tenx_config, self.submit_wdl)
        self.assertIn(b'10x/adapter.wdl', s4.wdl_file)

    @requests_mock.mock()
    def test_prepare_submission_does_not_cache_if_disabled(self, mock_request):
        self.set_up_mock(self.test_config, mock_request)
        prepare_submission = create_prepare_submission_function(False)
        prepare_submission(self.ss2_config, self.submit_wdl)
        requests_after_one_call = mock_request.call_count
        prepare_submission(self.ss2_config, self.submit_wdl)
        requests_after_two_calls = mock_request.call_count
        self.assertTrue(requests_after_two_calls > requests_after_one_call)


if __name__ == "__main__":
    unittest.main()
