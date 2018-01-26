from shared.utils.config import ConfigRestriction
from shared.utils.validator import is_not_empty, is_boolean, is_integer, is_config, is_db,\
    is_log, is_one_of_values, is_file_size, is_time_after, is_time_at


# name used for Logger
CLIENT_NAME = 'MQTT_CLIENT'

# region CONFIG RESTRICTIONS
# section Info
__general_config_path = ConfigRestriction(True, is_config)
__prefix = ConfigRestriction(False, is_not_empty)\
    .add_dependence('unique_name_source', 'mac')\
    .add_dependence('name')\
    .add_dependency_or('unique_name_source', 'name')        # optional (ps. works only if mac or name)
__unique_name_source = ConfigRestriction(True, is_one_of_values, 'default', 'mac')\
    .add_exclusionary_keys('name')
__name = ConfigRestriction(True, is_not_empty)\
    .add_exclusionary_keys('unique_name_source')
__clean_session = ConfigRestriction(False, is_boolean)      # optional (default exists)
__broker_host = ConfigRestriction(True, is_not_empty)
__broker_port = ConfigRestriction(True, is_integer)
__keepalive = ConfigRestriction(False, is_integer)          # optional (default exists)
# section Logger
__file_path = ConfigRestriction(False, is_log)              # optional
__depends_on = ConfigRestriction(False, is_one_of_values, 'nothing', 'size', 'time')\
    .add_dependence('file_path')                            # optional
__max_file_size = ConfigRestriction(False, is_file_size)\
    .add_dependence('depends_on', 'size')\
    .add_exclusionary_keys('time_after', 'time_at')         # optional
__time_after = ConfigRestriction(False, is_time_after)\
    .add_dependence('depends_on', 'time')\
    .add_exclusionary_keys('max_file_size', 'time_at')      # optional, NOT IMPLEMENTED
__time_at = ConfigRestriction(False, is_time_at)\
    .add_dependence('depends_on', 'time')\
    .add_exclusionary_keys('max_file_size', 'time_after')   # optional, NOT IMPLEMENTED
__rotate = ConfigRestriction(False, is_boolean)\
    .add_dependence('depends_on', 'size', 'time')\
    .add_dependence('max_files')                            # optional
__max_files = ConfigRestriction(False, is_integer)\
    .add_dependence('rotate', 'true')                       # optional
__print_log = ConfigRestriction(False, is_boolean)          # optional (default_exist)
__print_level = ConfigRestriction(False, is_not_empty)\
    .add_dependence('print_log', 'true')                    # optional (default_exist), NOT IMPLEMENTED
__write_level = ConfigRestriction(False, is_not_empty)\
    .add_dependence('file_path')                            # optional (default_exist), NOT IMPLEMENTED
# section Security
__accept_prefix = ConfigRestriction(False, is_not_empty)    # optional
__approval_required = ConfigRestriction(False, is_boolean)  # optional (default is FALSE)
__username = ConfigRestriction(False, is_not_empty)\
    .add_dependence('password')                             # optional
__password = ConfigRestriction(False, is_not_empty)\
    .add_dependence('username')                             # optional
__ca_file_path = ConfigRestriction(False, is_not_empty)     # optional
# section Database
__node_data_path = ConfigRestriction(True, is_db)
__accounts_path = ConfigRestriction(True, is_db)
# endregion

CONFIG_STRUCTURE = {
    'Info': {
        'general_config_path':  __general_config_path,
        'prefix':               __prefix,
        'unique_name_source':   __unique_name_source,
        'name':                 __name,
        'clean_session':        __clean_session,
        'broker_host':          __broker_host,
        'broker_port':          __broker_port,
        'keepalive':            __keepalive
    },
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
    'Security': {
        'accept_prefix':        __accept_prefix,
        'approval_required':    __approval_required,
        'username':             __username,
        'password':             __password,
        'ca_file_path':         __ca_file_path
    },
    'Database': {
        'node_data_path':       __node_data_path
    }
}
# PS (time_after and time_at won't work because it's not implemented, same goes for print and write
# levels too)


class Default:
    # Info
    CLEAN_SESSION = True
    KEEPALIVE = 60
    # Logger
    PRINT_LOG = False       # by default is False (in logger)
    # Security
    APPROVAL_REQUIRED = False

    # GLOBAL
    RECONNECT_AFTER = 2     # seconds
    EMPTY_STRING = ''


class MessageType:
    # Code that 2 or more mqtt clients share and they tell to opposite client/s what message means.
    # When sending code, it can tell others what to expect or how to parse rest of message. Same
    # goes for case when receiving code.
    NOT_OK = 0
    OK = 1
    CONFIG = 2


class MessageError:
    # Error codes that tell others what happened so they know what to do and how to handle specific
    # situations if they want to.
    INVALID_FORMAT = 1
    # MISSING_CONFIG = 2
    UNSUPPORTED_ID = 3
    UNKNOWN_CODE = 4
