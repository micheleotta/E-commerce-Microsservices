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

# consome o evento pagamento.aprovado
channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=pagamento.aprovado)

def callback(ch, method, properties, body):
    # processar evento se assinatura válida
    print(f" [x] {method.routing_key}:{body}")
    
    # emissao nota (???) e preparação de entrega
    
    # publicar pedido.enviado
    publish_event(publisher="entrega", channel=channel, event=pedido.enviado, conteudo="")


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()