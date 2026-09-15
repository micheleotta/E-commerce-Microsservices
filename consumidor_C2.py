#!/usr/bin/env python
import pika
import json

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo topic
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
result = channel.queue_declare(queue='consumidor_C2', exclusive=True)
queue_name = result.method.queue

# interessado em todas as categorias
channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key='promocao.categoria.*')


# recebe notificações sobre promoções de produtos
def callback(ch, method, properties, body):
    # consome promocoes
    promocao = json.loads(body)
    print(f"Promoção em {promocao['categoria']}: {promocao['produto']} com {promocao['desconto']}% de desconto!")


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    print("Consumidor C2 iniciado! Aguardando promoções...\n")
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()