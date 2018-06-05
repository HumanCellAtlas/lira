#!/usr/bin/env python
import unittest
import json
from copy import deepcopy
from lira import lira_config
import os
import logging


class TestStartupVerification(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """load the config file"""
        # Change to test directory, as tests may have been invoked from another dir
        dir = os.path.abspath(os.path.dirname(__file__))
        os.chdir(dir)
        with open('data/config.json', 'r') as f:
            cls.correct_test_config = json.load(f)

    def setUp(self):
        os.environ['caas_key'] = 'data/fake_caas_key.json'

    def test_correct_config_throws_no_errors(self):
        test_config = deepcopy(self.correct_test_config)

        try:  # make sure LiraConfig executes
            result = lira_config.LiraConfig(test_config)
        except BaseException as exception:
            self.fail(
                'LiraConfig constructor raised an exception: {exception}'
                .format(exception=exception))

        # check correct type
        self.assertIsInstance(result, lira_config.LiraConfig)

    def test_config_missing_required_field_throws_value_error(self):

        def delete_wdl_field(field_name):
            """return a config object whose first wdl config is missing a field"""
            test_config = deepcopy(self.correct_test_config)
            del test_config['wdls'][0][field_name]
            return test_config

        mangled_config = delete_wdl_field('subscription_id')
        self.assertRaises(ValueError, lira_config.LiraConfig, mangled_config)
        mangled_config = delete_wdl_field('workflow_name')
        self.assertRaises(ValueError, lira_config.LiraConfig, mangled_config)
        mangled_config = delete_wdl_field('wdl_link')
        self.assertRaises(ValueError, lira_config.LiraConfig, mangled_config)
        mangled_config = delete_wdl_field('wdl_static_inputs_link')
        self.assertRaises(ValueError, lira_config.LiraConfig, mangled_config)
        mangled_config = delete_wdl_field('analysis_wdls')
        self.assertRaises(ValueError, lira_config.LiraConfig, mangled_config)

    def test_error_thrown_when_analysis_wdl_is_not_list(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['wdls'][0]['analysis_wdls'] = 'bare string'
        with self.assertRaises(TypeError):
            lira_config.LiraConfig(test_config)

    def test_submit_and_hold_is_false_by_default(self):
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        self.assertFalse(config.submit_and_hold)

    def test_submit_and_hold_can_be_set_to_true(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['submit_and_hold'] = True
        config = lira_config.LiraConfig(test_config)
        self.assertTrue(config.submit_and_hold)

    def test_cache_wdls_is_true_by_default(self):
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        self.assertTrue(config.cache_wdls)

    def test_cache_wdls_can_be_set_to_false(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['cache_wdls'] = False
        config = lira_config.LiraConfig(test_config)
        self.assertFalse(config.cache_wdls)

    def test_werkzeug_logger_warning_by_default(self):
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        self.assertEqual(config.log_level_werkzeug, logging.WARNING)

    def test_connexion_validation_logger_info_by_default(self):
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        self.assertEqual(config.log_level_connexion_validation, logging.INFO)

    def test_werkzeug_logger_can_be_set_to_debug(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['log_level_werkzeug'] = logging.DEBUG
        config = lira_config.LiraConfig(test_config)
        self.assertEqual(config.log_level_werkzeug, logging.DEBUG)

    def test_connexion_validation_can_be_set_to_debug(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['log_level_connexion_validation'] = logging.DEBUG
        config = lira_config.LiraConfig(test_config)
        self.assertEqual(config.log_level_connexion_validation, logging.DEBUG)

    def test_stale_notification_timeout_defaults_to_zero(self):
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        self.assertEqual(config.stale_notification_timeout, 0)

    def test_stale_notification_timeout_can_be_set(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['stale_notification_timeout'] = 123
        config = lira_config.LiraConfig(test_config)
        self.assertEqual(config.stale_notification_timeout, 123)

    def test_hmac_keys_defaults_to_none(self):
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        self.assertFalse(hasattr(config, 'hmac_key'))

    def test_hmac_key_can_be_set(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['hmac_key'] = 'fake_key'
        config = lira_config.LiraConfig(test_config)
        self.assertEqual(config.hmac_key, 'fake_key'.encode('utf-8'))

    def test_notification_token_not_required(self):
        test_config = deepcopy(self.correct_test_config)
        test_config.pop('notification_token')
        config = lira_config.LiraConfig(test_config)

    def test_use_caas_defaults_to_false(self):
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        self.assertFalse(config.use_caas)

    def test_use_caas_can_be_set_to_true(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['use_caas'] = 'true'
        test_config['google_project'] = 'fake project'
        test_config['gcs_root'] = 'fake gcs root'
        config = lira_config.LiraConfig(test_config)
        self.assertTrue(config.use_caas)

    def test_using_caas_requires_google_project(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['use_caas'] = 'true'
        test_config['gcs_root'] = 'fake gcs root'
        with self.assertRaises(ValueError):
            config = lira_config.LiraConfig(test_config)

    def test_using_caas_requires_gcs_root(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['use_caas'] = 'true'
        test_config['google_project'] = 'fake project'
        with self.assertRaises(ValueError):
            config = lira_config.LiraConfig(test_config)

    def test_using_caas_requires_caas_key(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['use_caas'] = 'true'
        test_config['google_project'] = 'fake project'
        test_config['gcs_root'] = 'fake gcs root'
        del os.environ['caas_key']
        with self.assertRaises(ValueError):
            config = lira_config.LiraConfig(test_config)

    def test_cromwell_user_required_if_not_caas(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['use_caas'] = 'false'
        test_config['cromwell_password'] = 'fake password'
        test_config.pop('cromwell_user')
        with self.assertRaises(ValueError):
            config = lira_config.LiraConfig(test_config)

    def test_cromwell_password_required_if_not_caas(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['use_caas'] = 'false'
        test_config['cromwell_user'] = 'fake user'
        test_config.pop('cromwell_password')
        with self.assertRaises(ValueError):
            config = lira_config.LiraConfig(test_config)

    def test_user_and_password_not_required_when_using_caas(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['use_caas'] = 'true'
        test_config['google_project'] = 'fake project'
        test_config['gcs_root'] = 'fake gcs root'
        test_config.pop('cromwell_user')
        test_config.pop('cromwell_password')
        config = lira_config.LiraConfig(test_config)

    def test_collection_name_default_is_correct(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['env'] = 'fake-env'
        test_config.pop('collection_name', None)
        test_config['use_caas'] = 'true'
        test_config['google_project'] = 'fake project'
        test_config['gcs_root'] = 'fake gcs root'
        config = lira_config.LiraConfig(test_config)
        self.assertEqual(config.collection_name, 'lira-fake-env-workflows')

    def test_collection_name_can_be_set(self):
        test_config = deepcopy(self.correct_test_config)
        test_config['env'] = 'fake-env'
        test_config['collection_name'] = 'fake-collection-name'
        test_config['use_caas'] = 'true'
        test_config['google_project'] = 'fake project'
        test_config['gcs_root'] = 'fake gcs root'
        config = lira_config.LiraConfig(test_config)
        self.assertEqual(config.collection_name, 'fake-collection-name')

    def test_config_duplicate_wdl_raises_value_error(self):

        def add_duplicate_wdl_definition():
            """add the first wdl definition to the end of the 'wdls' json section"""
            test_config = deepcopy(self.correct_test_config)
            test_config['wdls'].append(test_config['wdls'][0])
            return test_config

        mangled_config = add_duplicate_wdl_definition()
        self.assertRaises(ValueError, lira_config.LiraConfig, mangled_config)

    def test_lira_config_exposes_all_methods_requested_in_notifications(self):
        # test that the calls made in notifications refer to attributes that
        # LiraConfig exposes
        test_config = deepcopy(self.correct_test_config)
        config = lira_config.LiraConfig(test_config)
        requested_lira_attributes = [
            'notification_token', 'wdls', 'cromwell_url', 'cromwell_user',
            'cromwell_password', 'MAX_CONTENT_LENGTH']
        for attr in requested_lira_attributes:
            self.assertTrue(hasattr(config, attr), 'missing attribute %s' % attr)

        # get an example wdl to test
        wdl = config.wdls[0]
        requested_wdl_attributes = [
            'subscription_id', 'wdl_link', 'workflow_name', 'wdl_static_inputs_link',
            'options_link']
        for attr in requested_wdl_attributes:
            self.assertTrue(hasattr(wdl, attr), 'missing attribute %s' % attr)


if __name__ == "__main__":
    unittest.main()
