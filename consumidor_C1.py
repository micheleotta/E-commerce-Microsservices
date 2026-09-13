#!/usr/bin/env python
import pika
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from microsservicos.produtos import categorias

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo topic
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
result = channel.queue_declare(queue='consumidor_C1', exclusive=True)
queue_name = result.method.queue

# eventos que consome -> categorias A e B
eventos = [f'promocao.categoria.{categorias[0]}', f'promocao.categoria.{categorias[1]}']
for evento in eventos:
    # subscribing, novo binding para cada evento de interesse
    channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key=evento)


# recebe notificações sobre promoções de produtos
def callback(ch, method, properties, body):
    # consome promocoes
    promocao = json.loads(body)
    print(f"Promoção em {promocao['categoria']}: {promocao['produto']} com {promocao['desconto']}% de desconto!")


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    print("Consumidor C1 iniciado! Aguardando promoções...")
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()
