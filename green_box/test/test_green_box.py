import unittest
import json
from copy import deepcopy
from .. import verify_config_json


# todo refactor into package for easier testing
# run tests from secondary-analysis folder with command:
# python2.7 -m green_box.test.test_startup

# load a json string representing a real json configuration.
correct_test_config = json.loads("""
{
  "notification_token": "test",
  "cromwell_user": "test",
  "cromwell_password": "test",
  "cromwell_url": "test",
  "provenance_script": "test",
  "wdls": [
    {
      "subscription_id": 222,
      "wdl_link": "gs://broad-dsde-mint-dev-teststorage/prepare_and_analyze_ss2_single_sample.wdl",
      "workflow_name": "PrepareAndAnalyzeSs2RsemSingleSample",
      "wdl_deps_link": "gs://broad-dsde-mint-dev-teststorage/ss2_single_sample_analysis_only.zip",
      "default_inputs_link": "gs://broad-dsde-mint-dev-teststorage/prepare_and_analyze_ss2_single_sample_default_inputs.json"
    },
    {
      "subscription_id": 333,
      "workflow_name": "PrepareAndAnalyzeMockSmartseq2",
      "wdl_link": "gs://broad-dsde-mint-dev-teststorage/prepare_and_analyze_mock_smartseq2.wdl",
      "default_inputs_link": "gs://broad-dsde-mint-dev-teststorage/prepare_and_analyze_mock_smartseq2_default_inputs.json",
      "wdl_deps_link": "gs://broad-dsde-mint-dev-teststorage/mock_smartseq2.zip"
    },
    {
      "subscription_id": 1,
      "wdl_link": "gs://broad-dsde-mint-dev-teststorage/wrapper_ss2_single_sample.wdl",
      "workflow_name": "WrapperSs2RsemSingleSample",
      "wdl_deps_link": "gs://broad-dsde-mint-dev-teststorage/ss2_single_sample_analysis_only.zip",
      "default_inputs_link": "gs://broad-dsde-mint-dev-teststorage/wrapper_ss2_single_sample_example_static.json"
    }
  ]
}
""")


class TestStartupVerification(unittest.TestCase):

    def test_correct_config_throws_no_errors(self):
        """a valid json will return None"""
        result = verify_config_json(correct_test_config)
        self.assertEqual(result, None, 'valid json unexpectedly failed verification')

    def test_config_missing_any_field_throws_value_error(self):

        def delete_wdl_field(field_name):
            """return a config object whose first wdl config is missing a field"""
            config = deepcopy(correct_test_config)
            del config['wdls'][0][field_name]
            return config

        mangled_config = delete_wdl_field('subscription_id')
        self.assertRaises(ValueError, verify_config_json, mangled_config)
        mangled_config = delete_wdl_field('workflow_name')
        self.assertRaises(ValueError, verify_config_json, mangled_config)
        mangled_config = delete_wdl_field('wdl_link')
        self.assertRaises(ValueError, verify_config_json, mangled_config)
        mangled_config = delete_wdl_field('default_inputs_link')
        self.assertRaises(ValueError, verify_config_json, mangled_config)
        mangled_config = delete_wdl_field('wdl_deps_link')
        self.assertRaises(ValueError, verify_config_json, mangled_config)

    def test_config_additional_fields_raises_value_error(self):

        def add_wdl_field(field_name, value):
            """return a config object whose first wdl config has an extra field"""
            config = deepcopy(correct_test_config)
            config['wdls'][0][field_name] = value
            return config

        mangled_config = add_wdl_field('foo', 'bar')
        self.assertRaises(ValueError, verify_config_json, mangled_config)

    def test_config_duplicate_field_raises_value_error(self):

        def add_duplicate_wdl_definition():
            """add the first wdl definition to the end of the 'wdls' json section"""
            config = deepcopy(correct_test_config)
            config['wdls'].append(config['wdls'][0])
            return config

        mangled_config = add_duplicate_wdl_definition()
        self.assertRaises(ValueError, verify_config_json, mangled_config)

    def test_config_incorrect_gs_link_raises_value_error(self):

        def mangle_gs_link(key):
            """mangle the first wdl config's gs endpoint for key"""
            config = deepcopy(correct_test_config)
            config['wdls'][0][key] = 'gs://broad-dsde-mint-dev/not-a-real-file.tar'
            return config

        mangled_config = mangle_gs_link('wdl_link')
        self.assertRaises(ValueError, verify_config_json, mangled_config)


if __name__ == "__main__":
    unittest.main()
