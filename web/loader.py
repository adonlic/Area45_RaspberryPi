from shared.utils.log import Logger
from shared.utils.object_holder import ObjectHolder
from shared.utils.config import ConfigManager, ConfigCache
from shared.data.models.node_data import Base as NodeBase
from shared.data.handlers.node_data import DBHandler as NodeHandler

from web.constant import WEB_NAME, CONFIG_STRUCTURE
from web.data.accounts import Base as AccountBase
from web.data.accounts import DBHandler as AccountHandler


logger = ObjectHolder()
node_db_handler = ObjectHolder()
account_db_handler = ObjectHolder()


def load(cwd):
    config_manager = ConfigManager().get_instance()
    config_cache = ConfigCache.get_instance()
    result = dict()

    config, message = config_manager.read(cwd, CONFIG_STRUCTURE)
    print("{}:\t{}".format(WEB_NAME, message))

    if config is not None:
        # load only this config, no need for MAC address from general config...
        config_cache.load(None, config)

        # region LOAD LOGGER
        filename = ''
        depends_on = Logger.DEPENDS_ON_NOTHING
        max_file_size = ''
        rotate = False
        max_files = 1
        print_log = False   # set False as default

        if 'file_path' in config.keys():
            filename = config['file_path']

            if 'depends_on' in config.keys():
                if config['depends_on'] == 'size':
                    depends_on = Logger.DEPENDS_ON_SIZE
                elif config['depends_on'] == 'time':
                    depends_on = Logger.DEPENDS_ON_TIME
                if 'max_file_size' in config.keys():
                    max_file_size = config['max_file_size']
                if 'rotate' in config.keys():
                    if config['rotate'] == 'true':
                        rotate = True
                    else:
                        rotate = False
                    max_files = config['max_files']
        if 'print_log' in config.keys():
            if config['print_log'] == 'true':
                print_log = True
            else:
                print_log = False

        logger_obj = Logger(WEB_NAME, filename, depends_on, max_file_size,
                            rotate=rotate, max_files=max_files, print_log=print_log)
        logger.hold(logger_obj)
        # endregion

        NodeHandler.init(NodeBase, config['node_data_path'])
        node_db_handler_obj = NodeHandler.get_instance()
        node_db_handler.hold(node_db_handler_obj)

        AccountHandler.init(AccountBase, config['accounts_path'])
        account_db_handler_obj = AccountHandler.get_instance()
        account_db_handler.hold(account_db_handler_obj)

        return True, result
    else:
        return False, None
