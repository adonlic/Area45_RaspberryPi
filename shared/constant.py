from shared.utils.config import ConfigRestriction
from shared.utils.validator import is_not_empty, is_one_of_values


CONFIG_NAME = 'UTILS_CONFIG'
INFO_PROVIDER_NAME = 'INFO_PROVIDER'

__local_address = ConfigRestriction(True, is_not_empty)
__local_address_type = ConfigRestriction(True, is_one_of_values, '2', '23')

CONFIG_STRUCTURE = {
    'Info': {
        'local_address': __local_address,
        'local_address_type': __local_address_type
    }
}
