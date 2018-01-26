import os
import time

from socket import gaierror

from paho.mqtt import client as mqttc

from shared.utils.validator import is_integer, is_double

from mqtt.constant import Default, MessageType
from mqtt.loader import load, logger, config_cache, cache, node_db_handler


def start():
    ok, info = load(os.getcwd())

    if not ok:
        return

    # create client and setup and try to connect until connected
    if info['client_id'] == '':
        # if unique_name_source = default...
        mqtt_client = mqttc.Client(clean_session=info['clean_session'])
    else:
        mqtt_client = mqttc.Client(client_id=info['client_id'], clean_session=info['clean_session'])
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    # flag below is used to stop printing same thing again and again, for console same as for logger
    error_already_written = False

    while True:
        try:
            # connecting to broker can fail if broker is not up or port is invalid
            if not error_already_written:
                logger.access().info("Trying to connect to '{}:{}' as {} with keepalive {}, {} second/s delay"
                                     .format(info['broker_host'], info['broker_port'], mqtt_client._client_id,
                                             info['keepalive'], Default.RECONNECT_AFTER))
            else:
                print("Trying to connect...")
            mqtt_client.connect(info['broker_host'], info['broker_port'], info['keepalive'])
        except ConnectionRefusedError:
            if not error_already_written:
                logger.access().info("MQTT server isn't up or broker address and/or port are invalid, "
                                     "will try to reconnect...")
                error_already_written = True

            time.sleep(Default.RECONNECT_AFTER)
            continue
        except TimeoutError:
            if not error_already_written:
                logger.access().info("Host is not responding, will try to reconnect...")
                error_already_written = True
            continue
        except gaierror:
            # this is internal error of paho mqtt framework ('giaerror' is an error that's implemented
            # in built-in Python 'socket' module, which paho mqtt uses)
            logger.access().info("Cannot resolve hostname, application will terminate")
            return

        # as this script runs in new thread, we can use loop_forever() function instead of loop_start()
        # because it will not create new thread, but block current one, which is already new thread...
        mqtt_client.loop_forever()


def on_connect(client, userdata, flags, rc):
    cache.client_connected()
    logger.access().info("Client connected on broker")

    # subscribe to 'start' theme each time client connects/reconnects on broker
    client.subscribe("start", qos=1)


def on_disconnect(client, userdata, rc):
    cache.client_disconnected()
    logger.access().info("Client disconnected from broker")


def on_message(client, userdata, message):
    if message.topic == 'start':
        logger.access().warning("Upcoming sync/registration request, data: '{}'".format(message.payload.decode()))
        node_msg = message.payload.decode().split(';')

        # if there's something and first parameter is not empty string...
        if len(node_msg) >= 1 and node_msg[0] != '':
            # first parameter should ALWAYS be node's id!
            if __validate_node_id(node_msg[0]):
                logger.access().info("Node '{}' has successfully been verified".format(node_msg[0]))
                if cache.in_cache(node_msg[0]):
                    # return status OK (code = 1) at node
                    client.publish(node_msg[0], MessageType.OK, qos=1)
                    logger.access().info("Confirmation sent to node '{}'".format(node_msg[0]))
                elif node_db_handler.access().node_exists(node_msg[0]):
                    __prepare_for_the_user(client, node_msg[0])
                    logger.access().info("Confirmation sent to node '{}'".format(node_msg[0]))
                else:
                    # logger.access().info("")
                    if len(node_msg) == 1:
                        # request config (code = 2) because there's no config for given node
                        client.publish(node_msg[0], MessageType.CONFIG, qos=1)
                    else:
                        # if there are more parameters...(it could be config that node sent)
                        # if it's empty, it'll return false because function works like that, same goes if
                        # it's not integer...
                        integer, message = is_integer(node_msg[1])

                        if integer:
                            code = int(node_msg[1])

                            # if incoming message is config...
                            if code == MessageType.CONFIG:
                                # if there's 3rd parameter -> parse, else just ignore
                                if len(node_msg) > 2:
                                    # send node's components to parser (they'll be validated there too)
                                    parsed_conf = __parse_config(node_msg[2:])

                                    # if parse is successful, send data to DB, else ignore
                                    if parsed_conf is not None:
                                        # send data to DB
                                        node_db_handler.access().new_node_config(node_msg[0], parsed_conf)
                                        logger.access().info("Config setup for node '{}' is completed"
                                                             .format(node_msg[0]))
                                        __prepare_for_the_user(client, node_msg[0])
                                        logger.access().info("Confirmation sent to node '{}'".format(node_msg[0]))
    else:
        # other topics (not initialization/registration topic)
        topic = message.topic.split('/')

        # if there are at least 2 parameters: topic and id, and if first is topic, not just anyone, then
        # continue doing what it must be done...
        # topics: node-id/1, node-id/2/C, node-id/2/%
        if len(topic) >= 2 and cache.in_cache(topic[0]):
            node_id = topic[0]
            integer, err_message = is_integer(topic[1])

            if integer:
                component_id_used = int(topic[1])

                if len(topic) == 3:
                    measuring_unit = topic[2]
                    data = message.payload.decode()
                    integer, err_message = is_integer(data)
                    double, err_message2 = is_double(data)

                    # check if it's double value...
                    if integer or double:
                        value = float(data)
                        # send data to DB
                        node_db_handler.access().new_data(node_id, component_id_used, measuring_unit, value)

                # this part of code should be used for controlling stuff, not reading from sensors because
                # it's enough to have topic and component_id for it...


def __validate_node_id(node_id):
    if 'accept_prefix' in config_cache.config.keys():
        accept_prefix = config_cache.config['accept_prefix']

        # if node_id has prefix and at least one character that's different than others
        if len(accept_prefix) <= len(node_id) - 1:
            # if node's prefix isn't valid...
            if accept_prefix != node_id[:len(accept_prefix)]:
                return False
        else:
            return False

    # if there's no accept_prefix key or if there is and node has it, node has valid id...
    return True


def __prepare_for_the_user(client, node_id):
    config = node_db_handler.access().get_node_config(node_id)
    themes = __build_node_themes(node_id, config)
    cache.append_node(node_id)

    for theme in themes:
        cache.append_theme(node_id, theme)
        # subscribe to each theme with QoS = 0
        client.subscribe(theme)

    # return status OK
    client.publish(node_id, MessageType.OK, qos=1)


def __build_node_themes(node_id, config):
    themes = list()

    for component_id_used in config.keys():
        for measuring_unit in config[component_id_used]:
            themes.append('{}/{}/{}'.format(node_id, str(component_id_used), measuring_unit))

    return themes


def __parse_config(config_components):
    """
    result = (
        {
            type:           'senzor',
            id_used:        5,
            name:           'DHT22',
            value_types:    (
                {
                    value_type:         'temperatura',
                    measuring_unit:     'C',
                    measurement_period: 5
                }
            )
        },
        {
            type:           'senzor',
            id_used:        6,
            name:           'BME280',
            value_types:    (
                {
                    value_type:         'temperatura',
                    measuring_unit:     'C',
                    measurement_period: 6
                },
                {
                    value_type:         'vlaga',
                    measuring_unit:     '%',
                    measurement_period: 6
                }
            )
        }
    )
    :param config:
    :return:
    """

    components = list()

    # basically, for each component (components are divided with ';')...
    for component in config_components:
        component_sub_parts = component.split('|')

        # expecting at least 3 params (first 3 are basically component information, every other set of 3
        # params, if exist, are component's supported value types)
        if len(component_sub_parts) >= 3:
            component_type = component_sub_parts[0]
            id_used = component_sub_parts[1]
            name = component_sub_parts[2]   # can come empty

            components.append(
                {
                    'type':         component_type,
                    'id_used':      id_used,
                    'name':         name,
                    'value_types':  list()
                }
            )

            if len(component_sub_parts) > 3:
                # if config has valid format it would have every 3 params for each value type
                if len(component_sub_parts) % 3 == 0:
                    # for every other 3 params do...
                    current_index = 3

                    # ps. don't forget to position on first next value type after each iteration!
                    while current_index < len(component_sub_parts):
                        value_type = component_sub_parts[current_index]
                        measuring_unit = component_sub_parts[current_index + 1]
                        measurement_period = component_sub_parts[current_index + 2]

                        # add to last component...
                        components[-1]['value_types'].append(
                            {
                                'value_type':           value_type,
                                'measuring_unit':       measuring_unit,
                                'measurement_period':   measurement_period
                            }
                        )

                        current_index += 3
                else:
                    # even component part if it's good, it'll fail because the rest of config is not valid
                    return None
            # if it's only component information in config, then it's ok
        else:
            # if there isn't at least component information...
            # after component (3 places) are going component value types...
            return None

    return components


if __name__ == '__main__':
    start()
