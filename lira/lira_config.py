"""Classes that represent Lira configuration.
"""
import logging
import sys
import os


class Config(object):
    def __init__(self, config_dictionary, flask_config_values=None):
        """Abstract class that defines some useful configuration checks for Lira

        This object takes a dictionary of values and verifies them against expected_keys.
        It additionally accepts values from a flask config object, which it merges
        with the config_dictionary without doing additional checks.

        Args:
            config_dictionary (dict): Configuration values to be verified
            flask_config_values (flask.config.Config): flask.config.Config configuration values, for example
                those generated from a connexion App
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
        """Abstract property, must be defined by subclasses"""
        raise NotImplementedError

    def _verify_fields(self):
        """Verify config contains required fields"""

        given_keys = set(self.config_dictionary)
        extra_keys = given_keys - self.required_fields
        missing_keys = self.required_fields - given_keys
        if missing_keys:
            raise ValueError(
                'The following configuration is missing key(s): {keys}'
                ''.format(keys=', '.join(missing_keys))
            )
        if extra_keys:
            logger = logging.getLogger('{module_path}'.format(module_path=__name__))
            logger.info(
                'Configuration has non-required key(s): {keys}'
                ''.format(keys=', '.join(extra_keys))
            )

    def __eq__(self, other):
        return isinstance(other, WdlConfig) and hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        """Recursively collapse a config object into a hashable string"""
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

    # needed for flask-testing interface
    def get(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            return None


class WdlConfig(Config):
    """Subclass of Config to check WDL configurations"""

    @property
    def required_fields(self):
        return {
            'subscription_id',
            'wdl_link',
            'analysis_wdls',
            'workflow_name',
            'wdl_static_inputs_link',
            'options_link',
            'workflow_version',
        }

    def _verify_fields(self):
        super(WdlConfig, self)._verify_fields()
        if not isinstance(self.analysis_wdls, list):
            raise TypeError('analysis_wdls must be a list')

    def __str__(self):
        s = 'WdlConfig({0}, {1}, {2}, {3}, {4}, {5}, {6})'
        return s.format(
            self.subscription_id,
            self.wdl_link,
            self.analysis_wdls,
            self.workflow_name,
            self.wdl_static_inputs_link,
            self.options_link,
            self.workflow_version,
        )

    def __repr__(self):
        s = (
            'WdlConfig(subscription_id: {0},'
            ' wdl_link: {1},'
            ' analysis_wdls: {2},'
            ' workflow_name: {3},'
            ' wdl_static_inputs_link: {4},'
            ' options_link: {5},'
            ' workflow_version: {6})'
        )
        return s.format(
            self.subscription_id,
            self.wdl_link,
            self.analysis_wdls,
            self.workflow_name,
            self.wdl_static_inputs_link,
            self.options_link,
            self.workflow_version,
        )


class LiraConfig(Config):
    """Subclass of Config representing Lira configuration"""

    def __init__(self, config_object, *args, **kwargs):
        # Setting default values that can be overridden
        self.cache_wdls = True
        self.submit_and_hold = False

        # Setting the following log levels prevents log messages that
        # print query params in the log.
        # Werkzeug has INFO messages that log the url including query params of each request.
        # The Connexion validator has DEBUG messages that do the same.
        self.log_level_werkzeug = logging.WARNING
        self.log_level_connexion_validation = logging.INFO
        self.log_level_lira = logging.INFO

        # Send logs between log_level_lira and info (inclusive) to stdout.
        # If log_level_lira > INFO then nothing is sent to stdout.
        stdout_handler = logging.StreamHandler(sys.stdout)
        log_level_lira = config_object.get('log_level_lira')
        if log_level_lira is not None:
            self.log_level_lira = getattr(logging, log_level_lira)
        stdout_handler.setLevel(self.log_level_lira)
        stdout_handler.addFilter(MaxLevelFilter(logging.INFO))

        # Send logs at or above the greater of warning and log_level_lira to stderr.
        stderr_handler = logging.StreamHandler(sys.stderr)
        self.log_level_stderr = logging.WARNING
        if self.log_level_lira > logging.WARNING:
            self.log_level_stderr = self.log_level_lira
        stderr_handler.setLevel(self.log_level_stderr)

        logging.basicConfig(
            level=self.log_level_lira, handlers=[stdout_handler, stderr_handler]
        )

        # Configure log level for loggers that print query params.
        # Unless specified otherwise in Lira's config file, these will be set
        # at ERROR for werkzeug and INFO for connexion.decorators.validation
        # in order to suppress messages that include query params.
        logging.getLogger('werkzeug').setLevel(self.log_level_werkzeug)
        logging.getLogger('connexion.decorators.validation').setLevel(
            self.log_level_connexion_validation
        )

        env = config_object.get('env')
        if not config_object.get('google_pubsub_topic'):
            self.google_pubsub_topic = f'hca-notifications-{env}'

        # Check cromwell credentials
        use_caas = config_object.get('use_caas', None)
        if not use_caas:
            config_object['use_caas'] = False
        if config_object.get('use_caas'):
            if not config_object.get('collection_name'):
                self.collection_name = f'lira-{env}-workflows'
            caas_key = os.environ.get('caas_key')
            if not caas_key:
                raise ValueError(
                    'No service account json key provided for cromwell-as-a-service.'
                )
            self.caas_key = caas_key
            if not config_object.get('gcs_root'):
                raise ValueError(
                    'No gcs_root specified. You must specify a GCS path for workflow outputs to be written to when using CaaS.'
                )
        elif not config_object.get('cromwell_user') or not config_object.get(
            'cromwell_password'
        ):
            raise ValueError(
                'User and password required for {}'.format(
                    config_object.get('cromwell_url')
                )
            )

        # parse the wdls section
        wdl_configs = []
        try:
            for wdl in config_object[
                'wdls'
            ]:  # Parse wdls and instantiate WdlConfig objects
                wdl_configs.append(WdlConfig(wdl))
        except KeyError:
            raise ValueError('supplied config file must contain a "wdls" section.')
        self._verify_wdl_configs(wdl_configs)
        config_object[
            'wdls'
        ] = wdl_configs  # Store the WdlConfig objects back to wdls section

        if config_object.get('dry_run'):
            logger = logging.getLogger('{module_path}'.format(module_path=__name__))
            logger.warning(
                '***Lira is running in dry_run mode and will NOT launch any workflows***'
            )

        hmac_key = config_object.get('hmac_key')
        if hmac_key:
            config_object['hmac_key'] = hmac_key.encode('utf-8')

        # Legitimate notifications from blue box should be received by us shortly after being created.
        # If a notification's Date header is too old, we will refuse to accept it, configured by stale_notification_timeout.
        config_object['stale_notification_timeout'] = config_object.get(
            'stale_notification_timeout', 0
        )

        config_object['max_cromwell_retries'] = config_object.get(
            'max_cromwell_retries', 1
        )

        Config.__init__(self, config_object, *args, **kwargs)

    @property
    def required_fields(self):
        return {
            'env',
            'submit_wdl',
            'cromwell_url',
            'MAX_CONTENT_LENGTH',
            'wdls',
            'version',
            'dss_url',
            'ingest_url',
            'schema_url',
            'DOMAIN',
            'google_project'
        }

    @staticmethod
    def _verify_wdl_configs(wdl_configs):
        """Additional verification for wdl configurations"""
        if len(wdl_configs) != len(set(wdl_configs)):
            logger = logging.getLogger('{module_path}'.format(module_path=__name__))
            logger.warning('duplicate wdl definitions detected in config.json')

        if len(wdl_configs) != len(set([wdl.subscription_id for wdl in wdl_configs])):
            raise ValueError(
                'One or more wdl specifications contains a duplicated subscription ID '
                'but have non-identical configurations. Please check configuration file '
                'contents.'
            )

    def __str__(self):
        s = (
            'LiraConfig(environment: {0},'
            ' submit_wdl: {1},'
            ' cromwell_url: {2},'
            ' use_caas: {3},'
            ' MAX_CONTENT_LENGTH: {4},'
            ' wdls: {5},'
            ' lira_version: {6},'
            ' dss_url: {7},'
            ' ingest_url: {8},'
            ' schema_url: {9},'
            ' DOMAIN: {10},'
            ' google_project: {11}'
        )
        return s.format(
            self.env,
            self.submit_wdl,
            self.cromwell_url,
            ('use_caas: ' + self.use_caas),
            self.MAX_CONTENT_LENGTH,
            self.wdls,
            self.version,
            self.dss_url,
            self.ingest_url,
            self.schema_url,
            self.DOMAIN,
            self.google_project
        )

    def __repr__(self):
        s = (
            'LiraConfig(environment: {0},'
            ' submit_wdl: {1},'
            ' cromwell_url: {2},'
            ' use_caas: {3},'
            ' MAX_CONTENT_LENGTH: {4},'
            ' wdls: {5},'
            ' lira_version: {6},'
            ' dss_url: {7},'
            ' ingest_url: {8},'
            ' schema_url: {9},'
            ' DOMAIN: {10},'
            ' google_project: {11}'
        )
        return s.format(
            self.env,
            self.submit_wdl,
            self.cromwell_url,
            ('use_caas: ' + self.use_caas),
            self.MAX_CONTENT_LENGTH,
            self.wdls,
            self.version,
            self.dss_url,
            self.ingest_url,
            self.schema_url,
            self.DOMAIN,
            self.google_project
        )


class MaxLevelFilter(object):
    """Excludes logs above max_level"""

    def __init__(self, max_level):
        self.max_level = max_level

    def filter(self, log_record):
        return log_record.levelno <= self.max_level
