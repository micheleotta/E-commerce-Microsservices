#!/usr/bin/env python
import pika
import sys
import os
import re
import threading
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import pagamento, pedido, estoque, interesse, receive_event, publish_event, gerar_chaves
import estoque.bd.bakery_bd as bd # APAGAR DEPOIS

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="API REST Tradicional (Sem HATEOAS)")

# Habilita CORS para testes no Postman e Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pedidos = {}
pedidos_lock = threading.Lock()
prox_id = 1

gerar_chaves("principal")

# funções auxiliares
def publicar_evento(event, conteudo):
    """
    Conexão separada para a interação
    -> evitar bloqueio de conexão por demora na interação
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange="direct_logs", exchange_type="direct")
    publish_event(publisher="principal", channel=channel, event=event, conteudo=conteudo)
    connection.close()

def gerenciar_interesse(categoria, email, interessado):
    """
    Função para registrar e cancelar interesse de email em categoria
    """
    conteudo = {
        "categoria": categoria,
        "email": email,
        "interesse": interessado
    }
    
    # validar email
    padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(padrao, email):
        raise HTTPException(status_code=422, detail="Email inválido")
    
    # publicar interesse.promocao -> MS promocoes
    try:
        publicar_evento(event=interesse.promocao, conteudo=conteudo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado {e}")
    
    status = "registrado" if interessado else "cancelado"
    return {"mensagem": f"Interesse {status} na categoria {categoria}!"}


# O API Gateway deve disponibilizar endpoints REST para:
# listar produtos disponíveis em estoque
@app.get("/produtos")
def listar_produtos():
    """
    Retorna a lista de produtos disponíveis em estoque diretamente do MS Estoque (via REST)
    """
    try:
        response = requests.get("http://localhost:8001/produtos", timeout=5)
        response.raise_for_status()
        return response.json()
    
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Serviço de estoque indisponível")

# listar todas as categorias
@app.get("/categorias")
def listar_categorias():
    """
    Retorna a lista de categorias diretamente do MS Estoque (via REST)
    """
    try:
        response = requests.get("http://localhost:8001/categorias", timeout=5)
        response.raise_for_status()
        return response.json()
    
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Serviço de estoque indisponível")

# criar pedidos TODO
@app.post("/pedido")
def criar_pedido(body: dict):
    global prox_id
    
    produtos = body["produtos"]
    
    pedido_id = prox_id
    prox_id += 1
    
    novo_pedido = {
        "pedido_id": pedido_id,
        "produtos": [
            {
                "id_produto": produto["id_produto"],
                "nome": produto["nome"],
                "quantidade": produto["quantidade"],
                "preco": produto["preco"]
            } for produto in produtos
        ],
        "status": "pedido criado"
    }
    
    with pedidos_lock:
        pedidos[pedido_id] = novo_pedido
    
    publicar_evento(event=pedido.criado, conteudo=novo_pedido)
    print(f"\nPedido {pedido_id} criado!")
    return novo_pedido

# registrar interesse, informando o e-mail, em receber notificação sobre promoções de categorias;
@app.post("/interesse/{categoria}/{email}")
def registrar_interesse(categoria, email):
    """
    Registra email interessado em categoria
    """
    gerenciar_interesse(categoria=categoria, email=email, interessado=True)

# cancelar interesse em receber e-mail sobre.
@app.delete("/interesse/{categoria}/{email}")
def cancelar_interesse(categoria, email):
    """
    Cancelar interesse de email em categoria
    """
    gerenciar_interesse(categoria=categoria, email=email, interessado=False)


def callback(ch, method, properties, body):
    valida, conteudo = receive_event(consumer="principal", properties=properties, conteudo=body)
    evento = method.routing_key
    
    # processar evento somente se assinatura for válida!
    if valida:
        with pedidos_lock:
            # atualizar o status dos respectivos pedidos
            pedido_id = conteudo['pedido_id']
            if evento == pagamento.aprovado:
                status = "pagamento aprovado"
            elif evento == pedido.enviado:
                status = "pedido enviado"
            elif evento == pedido.estoque_ok:
                status = "estoque ok"
            # produto não disponível em estoque ou pagamento recusado -> pedido.excluido
            elif evento == estoque.indisponivel or evento == pagamento.recusado:
                motivos = {
                    estoque.indisponivel: "estoque indisponível",
                    pagamento.recusado: "pagamento recusado"
                }
                status = f"excluído - {motivos[evento]}"
                pedidos[pedido_id]["status"] = status
                publish_event(publisher='principal', channel=ch, event=pedido.excluido, conteudo=pedidos[pedido_id])
            pedidos[pedido_id]["status"] = status
            
        print(f"\nPedido {pedido_id} atualizado -> Status: {status}")
    else:
        print(f"\nAssinatura inválida, evento {evento} descartado!")


def consume():
    # conexão dedicada para consumir eventos
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # tipo Direct
    channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
    result = channel.queue_declare(queue='principal', exclusive=True)
    queue_name = result.method.queue

    # eventos que consome
    eventos = [pagamento.aprovado, pagamento.recusado, pedido.enviado, pedido.estoque_ok, estoque.indisponivel]
    for evento in eventos:
        # subscribing, novo binding para cada evento de interesse
        channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=evento)
    
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    thread_rabbit = threading.Thread(target=consume, daemon=True)
    thread_rabbit.start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
