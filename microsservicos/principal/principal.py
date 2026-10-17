#!/usr/bin/env python
import pika
import sys
import os
import re
import threading
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import pagamento, pedido, estoque, interesse, receive_event, publish_event, gerar_chaves

import uvicorn
import asyncio
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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

conexoes_sse = {}
loop = None

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

# criar pedido
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
@app.post("/interesse")
def registrar_interesse(body: dict):
    """
    Registra email interessado em categoria
    """

    categoria = body["categoria"]
    email = body["email"]

    return gerenciar_interesse(categoria=categoria, email=email, interessado=True)

# cancelar interesse em receber e-mail sobre.
@app.delete("/interesse/{categoria}/{email}")
def cancelar_interesse(categoria, email):
    """
    Cancelar interesse de email em categoria
    """
    return gerenciar_interesse(categoria=categoria, email=email, interessado=False)

async def notificar_cliente(pedido_id, mensagem):
    """
    Enviar atualizacoes do pedido para o cliente
    """
    pedido_id = str(pedido_id)
    if pedido_id in conexoes_sse:
        await conexoes_sse[pedido_id].put(mensagem)

@app.get("/sse/pedido/{pedido_id}")
async def sse_endpoint(pedido_id, request: Request):
    """Endpoint que mantém a conexão aberta transmitindo eventos."""
    fila_atualizacoes = asyncio.Queue()
    conexoes_sse[str(pedido_id)] = fila_atualizacoes

    async def evento_gerador():
        """Gerador assíncrono que envia as atualizacoes do pedido."""
        try:
            yield f"data: {json.dumps({ "message": "" })}\n\n"

            while True:
                # Espera por novas atualizacoes do pedido
                mensagem = await fila_atualizacoes.get()

                print(mensagem)

                # O formato padrão do SSE exige o prefixo "data: " e terminar com "\n\n"
                yield f"data: {mensagem}\n\n"

        except asyncio.CancelledError:
            print(f"\nErro no SSE do pedido {pedido_id}")
            pass
        finally:
            print(f"\nSSE finalizado para o pedido {pedido_id}")
            conexoes_sse.pop(str(pedido_id))

    return StreamingResponse(
        evento_gerador(),
        media_type="text/event-stream",  # Header obrigatório para SSE
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )

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
            
            asyncio.run_coroutine_threadsafe(
                notificar_cliente(pedido_id, json.dumps({
                    "status": status,
                    "message": f"Atualização do pedido {pedido_id}: {status}"
                })),
                loop
            )
        
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

@app.on_event("startup")
async def startup():
    global loop
    loop = asyncio.get_event_loop()
    
    thread_rabbit = threading.Thread(target=consume, daemon=True)
    thread_rabbit.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_graceful_shutdown=1)
