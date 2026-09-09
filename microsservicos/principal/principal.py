#!/usr/bin/env python
import pika
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from microsservicos.microsservicos import *

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo Direct
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

'''
pedido.criado  PUBLICA
- identificador do pedido
- os produtos
- quantidades
- informações necessárias para o processamento do pedido.
'''
'''
PRINTAR
interação com microsserviço principal
- visualizar produtos
- realizar pedidos
- excluir pedidos
- consultar pedidos e status
'''

# eventos que consome
eventos = [pagamento.aprovado, pagamento.recusado, pedido.enviado, pedido.estoque_ok, estoque.indisponivel]
for evento in eventos:
    # subscribing, novo binding para cada evento de interesse
    channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=evento)

def callback(ch, method, properties, body):
    receive_event()
    
    # atualizar o status dos respectivos pedidos
    
    # produto não disponível em estoque ou pagamento recusado -> publicar pedido.excluido
    if x == estoque.indisponivel or x == pagamento.recusado:
        publish_event(publisher="principal", channel=channel, event=pedido.excluido, conteudo="")


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()