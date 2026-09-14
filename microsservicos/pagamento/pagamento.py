#!/usr/bin/env python
import pika
import random
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from microsservicos import pedido, pagamento, publish_event, receive_event, gerar_chaves

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo Direct
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
result = channel.queue_declare(queue='pagamento', exclusive=True)
queue_name = result.method.queue

# consome o evento pedido.estoque_ok
channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=pedido.estoque_ok)

def callback(ch, method, properties, body):
    valida, conteudo = receive_event(method, properties, body)
    evento = method.routing_key
    
    # processar evento somente se assinatura for válida!
    if valida:
        pedido_id = conteudo['pedido_id']
        # processamento do pagamento por variáveis aleatórias
        aprovado = random.randint(1,101) % 2 == 0
        if(aprovado):
            # publicar um evento pagamento.aprovado
            publish_event(publisher="pagamento", channel=ch, event=pagamento.aprovado, conteudo=conteudo)
            print(f"\nPedido {pedido_id} -> pagamento aprovado!")
        else:
            # publicar um evento pagamento.recusado
            publish_event(publisher="pagamento", channel=ch, event=pagamento.recusado, conteudo=conteudo)
            print(f"\nPedido {pedido_id} -> pagamento recusado")
    else:
        print(f"Assinatura inválida, evento {evento} descartado!")


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    gerar_chaves("pagamento")
    print("Microsserviço de pagamento iniciado!")
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()