#!/usr/bin/env python
import unittest
import json
from copy import deepcopy
from lira import config
import os
import sys


class TestStartupVerification(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """load the config file"""
        # Change to test directory, as tests may have been invoked from another dir
        dir = os.path.abspath(os.path.dirname(__file__))
        os.chdir(dir)
        with open('config.json', 'rb') as f:
            cls.correct_test_config = json.load(f)

    def test_correct_config_throws_no_errors(self):
        test_config = deepcopy(self.correct_test_config)

        try:  # make sure ListenerConfig executes
            result = config.ListenerConfig(test_config)
        except BaseException as exception:
            self.fail(
                'ListenerConfig constructor raised an exception: {exception}'
                .format(exception=exception))

        # check correct type
        self.assertIsInstance(result, config.ListenerConfig)

    def test_config_missing_required_field_throws_value_error(self):

        def delete_wdl_field(field_name):
            """return a config object whose first wdl config is missing a field"""
            test_config = deepcopy(self.correct_test_config)
            del test_config['wdls'][0][field_name]
            return test_config

        mangled_config = delete_wdl_field('subscription_id')
        self.assertRaises(ValueError, config.ListenerConfig, mangled_config)
        mangled_config = delete_wdl_field('workflow_name')
        self.assertRaises(ValueError, config.ListenerConfig, mangled_config)
        mangled_config = delete_wdl_field('wdl_link')
        self.assertRaises(ValueError, config.ListenerConfig, mangled_config)
        mangled_config = delete_wdl_field('wdl_default_inputs_link')
        self.assertRaises(ValueError, config.ListenerConfig, mangled_config)
        mangled_config = delete_wdl_field('wdl_deps_link')
        self.assertRaises(ValueError, config.ListenerConfig, mangled_config)

    def test_config_duplicate_wdl_raises_value_error(self):

        def add_duplicate_wdl_definition():
            """add the first wdl definition to the end of the 'wdls' json section"""
            test_config = deepcopy(self.correct_test_config)
            test_config['wdls'].append(test_config['wdls'][0])
            return test_config

        mangled_config = add_duplicate_wdl_definition()
        self.assertRaises(ValueError, config.ListenerConfig, mangled_config)

    def test_listener_config_exposes_all_methods_requested_in_notifications(self):
        # test that the calls made in notifications refer to attributes that
        # ListenerConfig exposes
        test_config = config.ListenerConfig(self.correct_test_config)
        requested_listener_attributes = [
            'notification_token', 'wdls', 'cromwell_url', 'cromwell_user',
            'cromwell_password', 'MAX_CONTENT_LENGTH']
        for attr in requested_listener_attributes:
            self.assertTrue(hasattr(test_config, attr), 'missing attribute %s' % attr)

        # get an example wdl to test
        wdl = test_config.wdls[0]
        requested_wdl_attributes = [
            'subscription_id', 'wdl_link', 'workflow_name', 'wdl_default_inputs_link',
            'wdl_deps_link', 'options_link']
        for attr in requested_wdl_attributes:
            self.assertTrue(hasattr(wdl, attr), 'missing attribute %s' % attr)


if __name__ == "__main__":
    unittest.main()
