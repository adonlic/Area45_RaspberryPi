import paho.mqtt.client as mqtt_client
import random
import time
import time


def on_connect(client, userdata, flags, rc):
    print("Connected with status " + str(rc))

    client.subscribe("node-weatherSensor")


def on_disconnect(client, userdata, rc):
    print("Disconnected with status " + str(rc))


def on_publish(client, userdata, mid):
    pass


def on_message(client, userdata, message):
    print("NODE Received message '" + str(message.payload.decode()) + "' on topic '"
          + message.topic + "' with QoS " + str(message.qos))

    if int(message.payload.decode()) == 2:
        print("posalji broj 2")
        client.publish('start', 'node-weatherSensor;2', 1)
        # client.publish("weatherSensor", "2")


client = mqtt_client.Client("root-weatherSensor")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.on_message = on_message

client.connect("localhost", 1883, 60)
print("Test client connected! ;)")
client.loop_start()
# client.publish("start", "node-PRVI", 1)
client.publish('start', "node-50;2;senzor|5|DHT22|temperatura|C|5;senzor|6||temperatura|C|6|vlaga|%|6", 1)
while True:
    time.sleep(1)
    # print("iteracija gotova...")
    # client.publish('node-50/6/C', 4.5)
    client.publish('node-50/5/C', 24.5)
    client.publish('node-50/6/%', 78.0)
# client.loop_forever()


def start():
    # while True:
        client.publish("start", "node-PRVI", 1)

        # temperature sensor (GPIO 4)
        # client.publish("/esp8266/temperature", str(random.randrange(20, 26)))
        # humidity sensor (GPIO 5)
        # client.publish("/esp8266/humidity", str(random.randrange(80, 82)))
        # time.sleep(1)
