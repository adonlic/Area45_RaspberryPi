class MqttCache:
    __instance = None

    @staticmethod
    def init():
        MqttCache.__instance = MqttCache()

    @staticmethod
    def get_instance():
        if MqttCache.__instance is None:
            MqttCache.__instance = MqttCache()

        return MqttCache.__instance

    def __init__(self):
        self.__client_mac = ''
        self.__client_connected = False
        self.__node_themes = dict()

    def set_client_mac(self, mac):
        self.__client_mac = mac

    @property
    def is_connected(self):
        return self.__client_connected

    def client_connected(self):
        self.__client_connected = True

    def client_disconnected(self):
        self.__client_connected = False

    def append_node(self, node):
        self.__node_themes[node] = list()

    def append_theme(self, node, theme):
        self.__node_themes[node].append(theme)

    def in_cache(self, node):
        if node in self.__node_themes.keys():
            return True

        return False


class MeasurementsCache:
    __instance = None

    @staticmethod
    def init():
        MeasurementsCache.__instance = MeasurementsCache()

    @staticmethod
    def get_instance():
        if MeasurementsCache.__instance is None:
            MeasurementsCache.__instance = MeasurementsCache()

        return MeasurementsCache.__instance

    def __init__(self):
        self.__measurements = list()

    @property
    def size(self):
        return len(self.__measurements)

    def append_measurement(self, measurement):
        self.__measurements.append(measurement)

    def append_measurements(self, measurements):
        for measurement in measurements:
            self.__measurements.append(measurement)

    def clear(self):
        self.__measurements = list()
