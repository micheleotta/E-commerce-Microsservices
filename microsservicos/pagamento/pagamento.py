#!/usr/bin/env python
import pika
import sys
import os
import threading
import requests
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import pedido, pagamento, publish_event, receive_event, gerar_chaves

def consume():
    # conectar
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # tipo Direct
    channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
    result = channel.queue_declare(queue='pagamento', exclusive=True)
    queue_name = result.method.queue

    # consome o evento pedido.estoque_ok
    channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=pedido.estoque_ok)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    try:
        gerar_chaves("pagamento")
        print("Microsserviço de pagamento iniciado!")
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


def callback(ch, method, properties, body):
    valida, conteudo = receive_event(consumer="pagamento", properties=properties, conteudo=body)
    evento = method.routing_key
    
    # processar evento somente se assinatura for válida!
    if valida:
        pedido_id = conteudo['pedido_id']

        valor = 0
        for produto_pedido in conteudo['produtos']:
            valor += produto_pedido['preco'] * produto_pedido['quantidade']

        try:
            # Solicita a criação de uma cobrança ao Mock de Pagamento para este
            # gerar a URL de checkout, passando a sua URL de Webhook para retorno
            response = requests.post(
                "http://localhost:8100/api/pagamento",
                json={
                    "pedido_id": pedido_id,
                    "produtos": conteudo['produtos'],
                    "valor": valor,
                    "callback_url": f"http://localhost:8002/webhook/pagamento"
                },
                timeout=5
            )
            response.raise_for_status()
            print(f"\nPedido {pedido_id} -> pagamento iniciado")

            # Temporário
            publish_event(publisher="pagamento", channel=ch, event=pagamento.iniciado, conteudo=response.json())
            print(response.json())
        
        except requests.RequestException:
            publish_event(publisher="pagamento", channel=ch, event=pagamento.recusado, conteudo=conteudo)
            print(f"\nPedido {pedido_id} -> erro ao iniciar pagamento")
    else:
        print(f"Assinatura inválida, evento {evento} descartado!")


# Disponibiliza o endpoint HTTP para receber o Webhook do Mock de Pagamento com o status APROVADO ou RECUSADO.
app = FastAPI(title="Microsserviço de Pagamento")

class WebhookBody(BaseModel):
    pedido_id: int
    produtos: list
    aprovado: bool

@app.post("/webhook/pagamento")
def receber_webhook_pagamento(body: WebhookBody):
    conteudo = {
        "pedido_id": body.pedido_id,
        "produtos": body.produtos,
        "aprovado": body.aprovado
    }

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    if(body.aprovado):
        # publicar um evento pagamento.aprovado
        publish_event(publisher="pagamento", channel=channel, event=pagamento.aprovado, conteudo=conteudo)
        print(f"\nPedido {body.pedido_id} -> pagamento aprovado!")
    else:
        # publicar um evento pagamento.recusado
        publish_event(publisher="pagamento", channel=channel, event=pagamento.recusado, conteudo=conteudo)
        print(f"\nPedido {body.pedido_id} -> pagamento recusado")
    
    return {"mensagem": "Webhook recebido com sucesso!"}

if __name__ == "__main__":
    thread_rabbit = threading.Thread(target=consume, daemon=True)
    thread_rabbit.start()
    uvicorn.run(app, host="0.0.0.0", port=8002)