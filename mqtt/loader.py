from shared import constant as shared_constant
from shared.utils.log import Logger
from shared.utils.object_holder import ObjectHolder
from shared.utils.config import ConfigManager, ConfigCache
from shared.utils.info_provider import get_mac
from shared.data.models.node_data import Base as NodeBase
from shared.data.handlers.node_data import DBHandler as NodeHandler

from mqtt.constant import CLIENT_NAME, CONFIG_STRUCTURE, Default
from mqtt.cache import MqttCache, MeasurementsCache


"""
This script is used for reading config files and setting up application level variables
either one's that are based on application inter structure or based on information that's
pulled from config files.
"""


# init all required storage and handlers/managers
# logger = None   # will be assigned later in a client
logger = ObjectHolder()
config_manager = ConfigManager().get_instance()
config_cache = ConfigCache.get_instance()
cache = MqttCache.get_instance()
measurements_cache = MeasurementsCache.get_instance()
# required to use init because of constructor parameter!
node_db_handler = ObjectHolder()


def load(cwd):
    """
    Load config for client and config shared with web server, and put them in application
    storage. Additionally, read sections Info and Logger from client config because they
    are required before any other steps.

    :param cwd:
    :return:
    """
    result = dict()
    prefix = ''
    client_id = ''
    clean_session = Default.CLEAN_SESSION
    # broker_host = ''
    # broker_port = ''
    keepalive = Default.KEEPALIVE

    # raed client config
    config, message = config_manager.read(cwd, CONFIG_STRUCTURE)
    print("{}:\t{}".format(CLIENT_NAME, message))

    if config is not None:
        general_config, message = config_manager.read(config['general_config_path'], shared_constant.CONFIG_STRUCTURE)
        print("{}:\t{}".format(shared_constant.CONFIG_NAME, message))

        if general_config is not None:
            # save config to cache
            config_cache.load(general_config, config)

            # region LOAD SOME VALUES (all from Info section)
            # none of config keys can't exist if they're empty, so if they exist, we can use them
            if 'prefix' in config.keys():
                prefix = config['prefix']
            # find out what unique mqtt client name is needed
            if 'unique_name_source' in config.keys():
                if config['unique_name_source'] == 'mac':
                    mac, message = get_mac(general_config['local_address'], general_config['local_address_type'])
                    print(message)

                    if mac is None:
                        return False, None
                    # if mac exists program will go here...
                    cache.set_client_mac(mac)
                    client_id = mac
            elif 'name' in config.keys():
                # either 'unique_name_source' can exist or 'name'
                client_id = config['name']
            if 'clean_session' in config.keys():
                if config['clean_session'] == 'true':
                    clean_session = True
                else:
                    clean_session = False
            broker_host = config['broker_host']
            broker_port = int(config['broker_port'])
            if 'keepalive' in config.keys():
                keepalive = int(config['keepalive'])
            # endregion

            result['client_id'] = prefix + client_id
            result['clean_session'] = clean_session
            result['broker_host'] = broker_host
            result['broker_port'] = broker_port
            result['keepalive'] = keepalive

            # region LOAD LOGGER
            filename = ''
            depends_on = Logger.DEPENDS_ON_NOTHING
            max_file_size = ''
            rotate = False
            max_files = 1
            print_log = Default.PRINT_LOG

            if 'file_path' in config.keys():
                filename = config['file_path']

                if 'depends_on' in config.keys():
                    if config['depends_on'] == 'size':
                        depends_on = Logger.DEPENDS_ON_SIZE
                    elif config['depends_on'] == 'time':
                        depends_on = Logger.DEPENDS_ON_TIME
                    # by default, it already has 'DEPENDS_ON_NOTHING' (in logger)

                    if 'max_file_size' in config.keys():
                        max_file_size = config['max_file_size']
                    if 'rotate' in config.keys():
                        if config['rotate'] == 'true':
                            rotate = True
                        else:
                            rotate = False
                        # if rotate exists, then max_files should too...
                        max_files = config['max_files']
            if 'print_log' in config.keys():
                print_log = config['print_log']

            logger_obj = Logger(CLIENT_NAME, filename, depends_on, max_file_size,
                                rotate=rotate, max_files=max_files, print_log=print_log)
            logger.hold(logger_obj)
            # endregion

            NodeHandler.init(NodeBase, config['node_data_path'])
            node_db_handler_obj = NodeHandler.get_instance()
            node_db_handler.hold(node_db_handler_obj)

            return True, result
        else:
            return False, None
    else:
        return False, None
