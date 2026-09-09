#!/usr/bin/env python
import pika
import random
from microsservicos.microsservicos import *

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo Direct
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# consome o evento pedido.estoque_ok
channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=pedido.estoque_ok)

def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body}")
    
    # processamento do pagamento por variáveis aleatórias
    aprovado = random.randint() % 2 == 0
    if(aprovado):
        # publicar um evento pagamento.aprovado
        publish_event(publisher="pagamento", channel=channel, event=pagamento.aprovado, conteudo="")
    else:
        # publicar um evento pagamento.recusado
        publish_event(publisher="pagamento", channel=channel, event=pagamento.recusado, conteudo="")


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()