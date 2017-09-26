# not yet integrated; wanted to debug permissions first.

from . import verify_gs_link
import warnings

class WdlConfig:

    def __init__(self, config_dict):
        self._verify_fields(config_dict)
        self._subscription_id = config_dict['subscription_id']
        self._wdl_link = config_dict['wdl_link']
        self._workflow_name = config_dict['workflow_name']
        self._wdl_deps_link = config_dict['wdl_deps_link']
        self._default_inputs_link = config_dict['default_inputs_link']

    @staticmethod
    def _verify_fields(config_dict):
        """

        :param dict config_dict:
        :return:
        """
        expected_fields = {
            'subscription_id',
            'wdl_link',
            'workflow_name',
            'wdl_deps_link',
            'default_inputs_link'
        }

        wdl_keys = set(config_dict.keys())
        extra_keys = wdl_keys - expected_fields
        missing_keys = expected_fields - wdl_keys
        if missing_keys:
            raise ValueError('\nThe following WDL configuration is missing key(s): '
                             '{keys}\n{wdl}'
                             ''.format(wdl=config_dict, keys=', '.join(missing_keys)))
        if extra_keys:
            raise ValueError(
                '\nThe following WDL configuration has unexpected key(s): '
                '{keys}\n{wdl}'
                ''.format(wdl=config_dict, keys=', '.join(extra_keys)))

    @property
    def subscription_id(self):
        return self._subscription_id

    @property
    def wdl_link(self):
        return self._wdl_link

    @wdl_link.setter
    def wdl_link(self, value):
        verify_gs_link(value)
        self._wdl_link = value

    @property
    def workflow_name(self):
        return self._workflow_name

    @property
    def wdl_deps_link(self):
        return self._wdl_deps_link

    @wdl_deps_link.setter
    def wdl_deps_link(self, value):
        verify_gs_link(value)
        self._wdl_deps_link = value

    @property
    def default_inputs_link(self):
        return self._default_inputs_link

    @default_inputs_link.setter
    def default_inputs_link(self, value):
        verify_gs_link(value)
        self._default_inputs_link = value

    def __eq__(self, other):
        if not isinstance(other, WdlConfig):
            return False
        else:
            return True if hash(self) == hash(other) else False

    def __ne__(self, other):
        return not self.__eq__(other)

    def hash(self):
        return hash(''.join([
            self.subscription_id,
            self.wdl_link,
            self.wdl_deps_link,
            self.workflow_name,
            self.default_inputs_link
        ]))


class SubscriptionConfig:

    def __init__(self, config_json):
        self._wdls = [WdlConfig(c) for c in config_json['wdls']]
        self._notification_token = config_json['notification_token']
        self._cromwell_user = config_json['cromwell_user']
        self._cromwell_password = config_json['cromwell_password']
        self._cromwell_url = config_json['cromwell_url']
        self._provenance_script = config_json['provenance_script']

        # going to define dict container methods so that this class is accessible
        # as a dict
        self._dict = {
            'wdls': self.wdls,
            'notification_token': self._notification_token,
            'cromwell_user': self._cromwell_user,
            'cromwell_url': self._cromwell_url,
            'provenance_script': self._provenance_script
        }

    @property
    def wdls(self):
        return self._wdls

    @wdls.setter
    def wdls(self, wdl_configs):
        """verify that wdls are the correct format before allowing them to be set

        :param list wdl_configs:
        """
        if len(wdl_configs) != len(set(wdl_configs)):
            warnings.warn('duplicate wdl definitions detected in config.json')

        if len(wdl_configs) != len(set([wdl.subscription_id for wdl in wdl_configs])):
            raise ValueError(
                'One or more wdl specifications contains a duplicated subscription ID '
                'but have non-identical configurations. Please check configuration file '
                'contents.')

    # dict container attributes

    def __getitem__(self, item):
        return self._dict[item]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __iter__(self):
        return iter(self._dict)

    def keys(self):
        return self._dict.keys()

    def items(self):
        return self._dict.items()

    def values(self):
        return self._dict.values()

    def __len__(self):
        return len(self._dict)
