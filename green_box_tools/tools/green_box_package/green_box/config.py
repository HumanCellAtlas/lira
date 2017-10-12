import logging


class Config:

    def __init__(self, config_dictionary, flask_config_values=None):
        """abstract class that defines some useful configuration checks for the listener

        This object takes a dictionary of values and verifies them against expected_keys.
         It additionally accepts values from a flask config object, which it merges
         with the config_dictionary without doing additional checks.

        :param dict config_dictionary: configuration values to be verified
        :param flask_config_values: flask.config.Config configuration values, for example
          those generated from a connexxion App
        """
        self.config_dictionary = config_dictionary
        self._verify_fields()

        # make keys accessible in the namespace, grab any extra flask arguments
        for k, v in config_dictionary.items():
            setattr(self, k, v)
        if isinstance(flask_config_values, dict):
            for k, v in flask_config_values.items():
                setattr(self, k, v)

    @property
    def required_fields(self):
        """abstract property, must be defined by subclasses"""
        raise NotImplementedError

    def _verify_fields(self):
        """Verify wdl config contains valid entries for exactly the expected fields"""

        wdl_keys = set(self.config_dictionary)
        extra_keys = wdl_keys - self.required_fields
        missing_keys = self.required_fields - wdl_keys
        if missing_keys:
            raise ValueError(
                'The following WDL configuration is missing key(s): {keys}\n{wdl}'
                ''.format(wdl=self.config_dictionary, keys=', '.join(missing_keys)))
        if extra_keys:
            logging.warning(
                'The following WDL configuration has unexpected key(s): {keys}\n{wdl}'
                ''.format(wdl=self.config_dictionary, keys=', '.join(extra_keys)))

    def __eq__(self, other):
        return isinstance(other, WdlConfig) and hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_string(self):
        """recursively collapse a config object into a hashable string"""
        result = ''
        for v in self.required_fields:
            field_value = getattr(self, v)
            if isinstance(field_value, (str, unicode, int)):
                result += str(field_value)
            elif isinstance(field_value, Config):
                result += field_value.to_string()
            else:
                raise ValueError('Config fields must either be strings or config objects')
        return result

    def __hash__(self):
        return hash(self.to_string())

    # needed for flask interface
    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        return setattr(self, key, value)


class WdlConfig(Config):
    """subclass of Config to check WDL configurations"""

    @property
    def required_fields(self):
        return {
            'subscription_id',
            'wdl_link',
            'workflow_name',
            'wdl_deps_link',
            'wdl_default_inputs_link',
            'options_link'
        }


class ListenerConfig(Config):
    """subclass of Config to check listener configurations"""

    def __init__(self, json_config_object, *args, **kwargs):

        # parse the wdls section
        wdl_configs = []
        try:
            for wdl in json_config_object['wdls']:
                wdl_configs.append(WdlConfig(wdl))
        except KeyError:
            raise ValueError('supplied config file must contain a "wdls" section.')
        self._verify_wdl_configs(wdl_configs)
        json_config_object['wdls'] = wdl_configs

        Config.__init__(self, json_config_object, *args, **kwargs)

    @property
    def required_fields(self):
        return {
            'wdls',
            'notification_token',
            'cromwell_user',
            'cromwell_url',
            'cromwell_password',
            'MAX_CONTENT_LENGTH'
        }

    @staticmethod
    def _verify_wdl_configs(wdl_configs):
        """Additional verification for wdl configurations"""
        if len(wdl_configs) != len(set(wdl_configs)):
            logging.warning('duplicate wdl definitions detected in config.json')

        if len(wdl_configs) != len(set([wdl.subscription_id for wdl in wdl_configs])):
            raise ValueError(
                'One or more wdl specifications contains a duplicated subscription ID '
                'but have non-identical configurations. Please check configuration file '
                'contents.')
