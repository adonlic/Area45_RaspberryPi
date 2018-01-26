from shared.utils.config import ConfigRestriction
from shared.utils.validator import is_not_empty, is_boolean, is_integer, is_db,\
    is_log, is_one_of_values, is_file_size, is_time_after, is_time_at


WEB_NAME = 'WEB_SHARED'

# region CONFIG RESTRICTIONS
# section Logger
__file_path = ConfigRestriction(False, is_log)
__depends_on = ConfigRestriction(False, is_one_of_values, 'nothing', 'size', 'time')\
    .add_dependence('file_path')
__max_file_size = ConfigRestriction(False, is_file_size)\
    .add_dependence('depends_on', 'size')\
    .add_exclusionary_keys('time_after', 'time_at')
__time_after = ConfigRestriction(False, is_time_after)\
    .add_dependence('depends_on', 'time')\
    .add_exclusionary_keys('max_file_size', 'time_at')
__time_at = ConfigRestriction(False, is_time_at)\
    .add_dependence('depends_on', 'time')\
    .add_exclusionary_keys('max_file_size', 'time_after')
__rotate = ConfigRestriction(False, is_boolean)\
    .add_dependence('depends_on', 'size', 'time')\
    .add_dependence('max_files')
__max_files = ConfigRestriction(False, is_integer)\
    .add_dependence('rotate', 'true')
__print_log = ConfigRestriction(False, is_boolean)
__print_level = ConfigRestriction(False, is_not_empty)\
    .add_dependence('print_log', 'true')
__write_level = ConfigRestriction(False, is_not_empty)\
    .add_dependence('file_path')
# section Database
__node_data_path = ConfigRestriction(True, is_db)
__accounts_path = ConfigRestriction(True, is_db)
# endregion

CONFIG_STRUCTURE = {
    'Logger': {
        'file_path':            __file_path,
        'depends_on':           __depends_on,
        'max_file_size':        __max_file_size,
        'time_after':           __time_after,
        'time_at':              __time_at,
        'rotate':               __rotate,
        'max_files':            __max_files,
        'print_log':            __print_log,
        'print_level':          __print_level,
        'write_level':          __write_level
    },
    'Database': {
        'node_data_path': __node_data_path,
        'accounts_path': __accounts_path
    }
}
