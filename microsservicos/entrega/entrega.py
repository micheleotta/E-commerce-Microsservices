#!/usr/bin/env python
import pika
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import pedido, pagamento, publish_event, receive_event, gerar_chaves

def emitir_nota(conteudo):
    total = 0
    itens_nota = []
    
    for produto in conteudo['produtos']:
        nome = produto['nome']
        quantidade = produto['quantidade']
        preco = produto['preco']
        subtotal = preco * quantidade
        total += subtotal
        itens_nota.append({
            "nome": nome,
            "quantidade": quantidade,
            "preco_unitario": preco,
            "preco_total": subtotal
        })
        
    nota = {
        "pedido_id": conteudo['pedido_id'],
        "data_emissao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "itens": itens_nota,
        "total": total
    }
        
    print("\n========================")
    print("NOTA FISCAL")
    print("========================")
    print(f"Pedido: {nota['pedido_id']}")
    print(f"Data de emissão: {nota['data_emissao']}")
    print("\nItens:")
    for item in nota['itens']:
        print(f"- {item['nome']} {item['quantidade']}x | R$ {item['preco_unitario']} | Total = R$ {item['preco_total']}")
    print("\n------------------------")
    print(f"TOTAL PAGO: R$ {nota['total']}")
    print("========================")


# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo Direct
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
result = channel.queue_declare(queue='entrega', exclusive=True)
queue_name = result.method.queue

# consome o evento pagamento.aprovado
channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=pagamento.aprovado)


def callback(ch, method, properties, body):
    valida, conteudo = receive_event(consumer="entrega", properties=properties, conteudo=body)
    evento = method.routing_key
    
    # processar evento somente se assinatura for válida!
    if valida:
        # emissao nota e preparação de entrega
        print(f"\nEmitir nota pedido {conteudo['pedido_id']}")
        emitir_nota(conteudo)
        
        # publicar pedido.enviado
        publish_event(publisher="entrega", channel=ch, event=pedido.enviado, conteudo=conteudo)
        print(f"\nPreparando entrega pedido {conteudo['pedido_id']} -> pedido enviado")
    else:
        print(f"Assinatura inválida, evento {evento} descartado!")


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    gerar_chaves("entrega")
    print("Microsserviço de entrega iniciado!")
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()