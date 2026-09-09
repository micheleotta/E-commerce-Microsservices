#!/usr/bin/env python
import pika
from microsservicos.promocoes.promocoes import *

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo topic
channel.exchange_declare(exchange='logs', exchange_type='topic')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# interessado em todas as categorias
channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key='promocao.categoria.*')

def callback(ch, method, properties, body):
    # consome promocoes
    print(promocao)

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()