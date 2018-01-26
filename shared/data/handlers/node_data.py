from datetime import datetime

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import scoped_session, sessionmaker

from shared.data.models import node_data


class DBHandler:
    """
    Handles node_data database requests.
    """

    __instance = None

    @staticmethod
    def init(base, db_url):
        DBHandler.__instance = DBHandler(base, db_url)

    @staticmethod
    def get_instance():
        return DBHandler.__instance

    def __init__(self, base, db_url):
        # db_url = get_databases_folder(os.getcwd()) + '\\node_data.db'
        # self.__engine = create_engine('sqlite:///' + db_url, echo=True)
        self.__engine = create_engine('sqlite:///' + db_url)
        # self.__session = scoped_session(sessionmaker(autocommit=False,
        #                                              autoflush=False,
        #                                              bind=self.__engine))
        self.__session = scoped_session(sessionmaker(bind=self.__engine))

        # enable querying database through models
        # base.query = self.__session.query_property()

        # create tables if they don't exist (it handles all itself)
        base.metadata.create_all(self.__engine)

    def node_exists(self, node_id):
        # querying database through model
        # user = node_data.Node.query.filter(node_data.Node.id == node_id).first()
        user = self.__session.query(node_data.Node)\
            .filter(node_data.Node.id == node_id).first()
        # self.__session.remove()

        if user is None:
            return False

        return True

    # def create_node(self, node):
    #     self.__session.add(node)
    #     self.__session.commit()
    #
    # def delete_node(self, node):
    #     self.__session.delete(node)
    #     self.__session.commit()
    #
    # def create_component(self, component):
    #     self.__session.add(component)
    #     self.__session.commit()
    #
    # def create_value_type(self, value_type):
    #     self.__session.add(value_type)
    #     self.__session.commit()

    def get_node_config(self, node_id):
        """
        {id_used_1: [%, C],
         id_used_2: [%, C, Pa]
         }
        :param node_id:
        :return:
        """
        config = {}

        components = self.__session.query(node_data.Component)\
            .filter(node_data.Component.node_id == node_id).all()

        for component in components:
            config[component.id_used] = list()

            for component_value_type in component.component_value_types:
                # find config_update with biggest (newest) id because same component can have
                # multiple config updates
                newest_component_settings = None

                for component_settings in component_value_type.component_settingss:
                    if newest_component_settings is not None:
                        # if current component_settings is newer (it compares datetime) than old
                        # one, set current one as newest settings
                        if component_settings.config_update.updated_at > \
                                newest_component_settings.config_update.updated_at:
                            newest_component_settings = component_settings
                    else:
                        newest_component_settings = component_settings

                # there has to be settings, it's created when node registers etc.
                config[component.id_used].append(newest_component_settings.measuring_unit)

        return config

    def new_node_config(self, node_id, parsed_conf):
        """
        Inserts data into tables without checking handling unique constraints (database will
        return error if there's conflict).
        Also, it works only for creation, not update.

        :param node_id:     node name
        :param parsed_conf: list of node's components
        :return:
        """

        # sqlite needs explicit date and time because it accepts strings as datetime
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_update = node_data.ConfigUpdate(created_at, created_at)
        self.__session.add(config_update)
        node = node_data.Node(node_id, created_at, created_at)
        self.__session.add(node)
        self.__session.commit()
        # get config_update's id because it'll be required later (uniqueness by datetime)...
        # required for component_settings
        config_update_with_id = self.__session.query(node_data.ConfigUpdate)\
            .filter(node_data.ConfigUpdate.created_at == created_at).first()

        for component_info in parsed_conf:
            component_type = component_info['type']
            id_used = component_info['id_used']
            name = component_info['name']
            component = node_data.Component(node_id, id_used, component_type, created_at, created_at, name)
            self.__session.add(component)
            self.__session.commit()
            # get component id from database (each component is unique by 2 columns)...
            # it'll be required for component_value_type
            component_with_id = self.__session.query(node_data.Component) \
                .filter(and_(node_data.Component.node_id == node_id,
                             node_data.Component.id_used == id_used)).first()

            for value_type_info in component_info['value_types']:
                value_type = value_type_info['value_type']
                measuring_unit = value_type_info['measuring_unit']
                measurement_period = value_type_info['measurement_period']
                # now create value type...
                component_value_type = node_data.ComponentValueType(
                    component_with_id.id, value_type, created_at, created_at)
                self.__session.add(component_value_type)
                self.__session.commit()

                # now get component_value_type id from database (because it's required for component
                # setingss) - again, 2 unique columns
                component_value_type_with_id = self.__session.query(node_data.ComponentValueType)\
                    .filter(and_(node_data.ComponentValueType.component_id == component_with_id.id,
                                 node_data.ComponentValueType.value_type == value_type)).first()
                # now create component settings
                component_settings = node_data.ComponentSettings(
                    component_value_type_with_id.id, config_update_with_id.id,
                    measuring_unit, measurement_period, created_at)
                self.__session.add(component_settings)
                self.__session.commit()

    def new_data(self, node_id, component_id_used, measuring_unit, data):
        # measured_at will for now be the same
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        node = self.__session.query(node_data.Node).filter(node_data.Node.id == node_id).first()

        for component in node.components:
            if component.id_used == component_id_used:
                for component_value_type in component.component_value_types:
                    for component_settings in component_value_type.component_settingss:
                        if component_settings.measuring_unit == measuring_unit:
                            measurement = node_data.Measurement(
                                component_settings.id, data, created_at, created_at)
                            self.__session.add(measurement)
                            self.__session.commit()
                            # "exit all loops"
                            return

    def get_data(self, to_collector=False, only_not_confirmed=True, limit=None):
        result = {}
        result2 = []
        nodes = self.__session.query(node_data.Node).all()

        for node in nodes:
            if to_collector:
                for component in node.components:
                    for component_value_type in component.component_value_types:
                        # retrieve all config updates (even older one)
                        for component_settings in component_value_type.component_settingss:
                            # retrieve measurements
                            for measurement in component_settings.measurements:
                                result2.append({
                                    'node_id': node.id,
                                    'value': measurement.value,
                                    'measurement_type': component_value_type.value_type,
                                    'measuring_unit': component_settings.measuring_unit,
                                    'measured_at': measurement.measured_at
                                })
            else:
                return result2

        return result2
        #
        #     result[node.id] = dict()
        #
        #     for component in node.components:
        #         # now it's agreed with Collector site that it retrieves only one measurement
        #         # type per node, but in reality, node can have multiple sensors with same
        #         # measurement type...
        #         if to_collector:
        #             for component_value_type in component.component_value_types:
        #                 # if there are more components with same measurement type, append only
        #                 # first time it appears, ignore other appearances of same measurement
        #                 # type...
        #                 if component_value_type.value_type not in result[node.id].keys():
        #                     result[node.id][component_value_type.value_type] = dict()
        #                     # retrieve all config updates (even older one)
        #                     for component_settings in component_value_type.component_settingss:
        #                         result[node.id][component_value_type.value_type]['measuring_unit'] = \
        #                             component_settings.measuring_unit
        #                         result[node.id][component_value_type.value_type]['measurement_period'] = \
        #                             component_settings.measurement_period
        #                         result[node.id][component_value_type.value_type]['data'] = list()
        #
        #                         # retrieve measurements
        #                         for measurement in component_settings.measurements:
        #                             result[node.id][component_value_type.value_type]['data'].append(dict())
        #                             result[node.id][component_value_type.value_type]['data'][-1]['value'] = \
        #                                 measurement.value
        #                             result[node.id][component_value_type.value_type]['data'][-1]['measured_at'] = \
        #                                 measurement.measured_at
        #         else:
        #             pass
        #
        # return result

    def get_nodes(self):
        result = {
            'nodes': list()
        }
        nodes = self.__session.query(node_data.Node).all()

        for node in nodes:
            result['nodes'].append(node.id)

        return result

    def get_node_info(self, node_id, limit_result=None):
        # lazy load is enabled so it won't download measurements data
        node = self.__session.query(node_data.Node).filter(node_data.Node.id == node_id).first()

        # this shouldn't be called if node doesn't exist, but we must check if node exists
        # because someone could delete it from database in meanwhile, while retrieving it...
        if node is not None:
            result = {
                'id': node.id,
                'alias': node.alias,
                'components': list()
            }

            for component in node.components:
                # append new component to node (new sensor or switch)
                result['components'].append({
                    'id_used': component.id_used,
                    'type': component.type,
                    'name': component.name,
                    'alias': component.alias,
                    'value_types': list()
                })

                for component_value_type in component.component_value_types:
                    # save component's value types data to last list item, because it's "fresh"
                    # component...
                    result['components'][-1]['value_types'].append({
                        'value_type': component_value_type.value_type,
                        'alias': component_value_type.alias
                    })
                    # get measuring unit and measurement period with newest config
                    newest_component_settings = None

                    for component_settings in component_value_type.component_settingss:
                        if newest_component_settings is not None:
                            if component_settings.config_update.created_at > \
                                    newest_component_settings.config_update.created_at:
                                newest_component_settings = component_settings
                        else:
                            newest_component_settings = component_settings

                    # as we have newest config now, append it to value_types settings...
                    result['components'][-1]['value_types'][-1]['measuring_unit'] = \
                        newest_component_settings.measuring_unit
                    result['components'][-1]['value_types'][-1]['measurement_period'] = \
                        newest_component_settings.measurement_period
                    result['components'][-1]['value_types'][-1]['settings_valid_from'] = \
                        newest_component_settings.created_at

            return True, result

        return False, None

    # def get_data(self, node_id, get_last=None):
    #     pass
