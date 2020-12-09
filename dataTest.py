import paho.mqtt.client as mqtt

################################
##### MQTT FUNCTIONS ###########
################################
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connecting to server - "+str(rc))
    client.subscribe("data")

def on_message(client, userdata, msg):
    print(f"Received data: {msg.topic} - {str(msg.payload)}")

def on_publish(client, obj, mid):
    print("Sent data: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(client))

client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = on_subscribe
client.on_publish = on_publish
client.connect("localhost", 1883, 60)
client.publish("data", 42)
client.loop_forever()


