#!/usr/bin/env python
import unittest
import json
from copy import deepcopy
from listener_utils.listener_utils import ListenerConfig


class TestStartupVerification(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """load the config file"""
        with open('config.json', 'rb') as f:
            cls.correct_test_config = json.load(f)

    def test_correct_config_throws_no_errors(self):
        config = deepcopy(self.correct_test_config)

        try:  # make sure ListenerConfig executes
            result = ListenerConfig(config)
        except BaseException as exception:
            self.fail(
                'ListenerConfig constructor raised an exception: {exception}'
                .format(exception=exception))

        # check correct type
        self.assertIsInstance(result, ListenerConfig)

    def test_config_missing_required_field_throws_value_error(self):

        def delete_wdl_field(field_name):
            """return a config object whose first wdl config is missing a field"""
            config = deepcopy(self.correct_test_config)
            del config['wdls'][0][field_name]
            return config

        mangled_config = delete_wdl_field('subscription_id')
        self.assertRaises(ValueError, ListenerConfig, mangled_config)
        mangled_config = delete_wdl_field('workflow_name')
        self.assertRaises(ValueError, ListenerConfig, mangled_config)
        mangled_config = delete_wdl_field('wdl_link')
        self.assertRaises(ValueError, ListenerConfig, mangled_config)
        mangled_config = delete_wdl_field('wdl_default_inputs_link')
        self.assertRaises(ValueError, ListenerConfig, mangled_config)
        mangled_config = delete_wdl_field('wdl_deps_link')
        self.assertRaises(ValueError, ListenerConfig, mangled_config)

    def test_config_duplicate_wdl_raises_value_error(self):

        def add_duplicate_wdl_definition():
            """add the first wdl definition to the end of the 'wdls' json section"""
            config = deepcopy(self.correct_test_config)
            config['wdls'].append(config['wdls'][0])
            return config

        mangled_config = add_duplicate_wdl_definition()
        self.assertRaises(ValueError, ListenerConfig, mangled_config)

    def test_listener_config_exposes_all_methods_requested_in_notifications(self):
        # test that the calls made in notifications refer to attributes that
        # ListenerConfig exposes
        config = ListenerConfig(self.correct_test_config)
        requested_listener_attributes = [
            'notification_token', 'wdls', 'cromwell_url', 'cromwell_user',
            'cromwell_password', 'MAX_CONTENT_LENGTH']
        for attr in requested_listener_attributes:
            self.assertTrue(hasattr(config, attr), 'missing attribute %s' % attr)

        # get an example wdl to test
        wdl = config.wdls[0]
        requested_wdl_attributes = [
            'subscription_id', 'wdl_link', 'workflow_name', 'wdl_default_inputs_link',
            'wdl_deps_link', 'options_link']
        for attr in requested_wdl_attributes:
            self.assertTrue(hasattr(wdl, attr), 'missing attribute %s' % attr)


if __name__ == "__main__":
    unittest.main()
