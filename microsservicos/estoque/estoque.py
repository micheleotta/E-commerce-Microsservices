#!/usr/bin/env python
import pika
from microsservicos.microsservicos import *

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo Direct
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# eventos que consome
eventos = [pedido.criado, pedido.excluido]
for evento in eventos:
    # subscribing, novo binding para cada evento de interesse
    channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=evento)

def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body}")
    
    # se pedido.criado -> verificar disponibilidade
    # realizar reserva/baixa estoque e publicar pedido.estoque_ok
    publish_event(publisher="estoque", channel=channel, event=pedido.estoque_ok, conteudo="")
    # se não disponível -> estoque.indisponivel
    publish_event(publisher="estoque", channel=channel, event=pedido.indisponivel, conteudo="")
    
    # se pedido.excluido -> devolver ao estoque produtos reservados
    if x == pedido.excluido:
        estoque += devolvido # mudar


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()