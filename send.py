#!/usr/bin/env python
import pika
import json
import time

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='sensorData')

channel.basic_publish(exchange='', routing_key='sensorData', body=json.dumps(
    {
        'data': 'temperature',
        'time': time.time(),
        'value': 32
    }
))
print(" [x] Sent 'Hello World!'")
connection.close()
