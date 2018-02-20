"""Classes that represent Lira configuration.
"""
import logging


class Config(object):

    def __init__(self, config_dictionary, flask_config_values=None):
        """abstract class that defines some useful configuration checks for Lira 

        This object takes a dictionary of values and verifies them against expected_keys.
         It additionally accepts values from a flask config object, which it merges
         with the config_dictionary without doing additional checks.

        :param dict config_dictionary: configuration values to be verified
        :param flask_config_values: flask.config.Config configuration values, for example
          those generated from a connexxion App
        """
        self.config_dictionary = config_dictionary

        # make keys accessible in the namespace, grab any extra flask arguments
        for k, v in config_dictionary.items():
            setattr(self, k, v)
        if isinstance(flask_config_values, dict):
            for k, v in flask_config_values.items():
                setattr(self, k, v)

        self._verify_fields()

    @property
    def required_fields(self):
        """abstract property, must be defined by subclasses"""
        raise NotImplementedError

    def _verify_fields(self):
        """Verify config contains required fields"""

        given_keys = set(self.config_dictionary)
        extra_keys = given_keys - self.required_fields
        missing_keys = self.required_fields - given_keys
        if missing_keys:
            raise ValueError(
                'The following configuration is missing key(s): {keys}'
                ''.format(keys=', '.join(missing_keys)))
        if extra_keys:
            logger = logging.getLogger('Lira | {module_path}'.format(module_path=__name__))
            logger.info(
                'Configuration has non-required key(s): {keys}'
                ''.format(keys=', '.join(extra_keys)))

    def __eq__(self, other):
        return isinstance(other, WdlConfig) and hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        """recursively collapse a config object into a hashable string"""
        result = ''
        for v in self.required_fields:
            field_value = getattr(self, v)
            result += str(field_value)
        return result

    def __hash__(self):
        return hash(str(self))

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
            'analysis_wdls',
            'workflow_name',
            'wdl_static_inputs_link',
            'options_link'
        }

    def _verify_fields(self):
        super(WdlConfig, self)._verify_fields()
        if not isinstance(self.analysis_wdls, list):
            raise TypeError('analysis_wdls must be a list')

    def __str__(self):
        s = 'WdlConfig({0}, {1}, {2}, {3}, {4}, {5})'
        return s.format(self.subscription_id, self.wdl_link, self.analysis_wdls,
            self.workflow_name, self.wdl_static_inputs_link, self.options_link)

class LiraConfig(Config):
    """subclass of Config representing Lira configuration"""

    def __init__(self, config_object, *args, **kwargs):
        logger = logging.getLogger('Lira | {module_path}'.format(module_path=__name__))

        # Setting default values that can be overridden
        self.cache_wdls = True

        # Setting the following log levels prevents log messages that
        # print query params in the log.
        # Werkzeug has INFO messages that log the url including query params of each request.
        # The Connexion validator has DEBUG messages that do the same.
        self.log_level_werkzeug = 'WARNING'
        self.log_level_connexion_validation = 'INFO'

        # parse the wdls section
        wdl_configs = []
        try:
            for wdl in config_object['wdls']:
                wdl_configs.append(WdlConfig(wdl))
        except KeyError:
            raise ValueError('supplied config file must contain a "wdls" section.')
        self._verify_wdl_configs(wdl_configs)
        config_object['wdls'] = wdl_configs

        if config_object.get('dry_run'):
            logger.warning('***Lira is running in dry_run mode and will NOT launch any workflows***')

        Config.__init__(self, config_object, *args, **kwargs)

    @property
    def required_fields(self):
        return {
            'env',
            'submit_wdl',
            'cromwell_url',
            'cromwell_user',
            'cromwell_password',
            'notification_token',
            'MAX_CONTENT_LENGTH',
            'wdls'
        }

    @staticmethod
    def _verify_wdl_configs(wdl_configs):
        """Additional verification for wdl configurations"""
        if len(wdl_configs) != len(set(wdl_configs)):
            logger = logging.getLogger('Lira | {module_path}'.format(module_path=__name__))
            logger.warning('duplicate wdl definitions detected in config.json')

        if len(wdl_configs) != len(set([wdl.subscription_id for wdl in wdl_configs])):
            raise ValueError(
                'One or more wdl specifications contains a duplicated subscription ID '
                'but have non-identical configurations. Please check configuration file '
                'contents.')

    def __str__(self):
        s = 'LiraConfig({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7})'
        return s.format(self.env, self.submit_wdl, self.cromwell_url,
            '(cromwell_user)', '(cromwell_password)', '(notification_token)',
            self.MAX_CONTENT_LENGTH, self.wdls)
