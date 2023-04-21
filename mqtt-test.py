import json
import time
import paho.mqtt.client as paho
import base64
import ssl

clients_alive = {}
debug = True

def on_message(client, userdata, message):
    print(message.payload)

def on_log(client, userdata, level, buf):
    if debug:
        print("log: ", buf)

def on_connect(client, userdata, flags, rc):
    pass

client = paho.Client()
client.on_message = on_message
client.on_log = on_log
client.on_connect = on_connect
#ssl_context = ssl.create_default_context()
#client.tls_set(cert_reqs=ssl.CERT_NONE)
#client.tls_insecure_set(True)
client.connect("mq.hosting.csta.cisco.com", 8443, 60)
client.subscribe("cubelight/updates")
client.subscribe("cubelight/command")
client.loop_forever()
