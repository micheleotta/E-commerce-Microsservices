#!/usr/bin/env python
import pika
import sys
import os
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from produtos import produtos
from shared import pagamento, pedido, estoque, receive_event, publish_event, gerar_chaves

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

# O API Gateway deve disponibilizar endpoints REST para:
# • (0,1) listar produtos disponíveis em estoque;
# • (0,1) criar pedidos;
# • (0,1) registrar interesse, informando o e-mail, em receber notificação sobre promoções de categorias;
# • (0,1) cancelar interesse em receber e-mail sobre.

@app.get("/produtos")
def listar_produtos():
    """Retorna a lista de produtos cadastrados sem o objeto _links"""
    produtos_list = [
        {
            "id": produto.get_id(),
            "nome": produto.get_nome(),
            "categoria": produto.get_categoria(),
            "preco": produto.get_preco()
        }
        for produto in produtos
    ]

    return {
        "total": len(produtos_list),
        "produtos": produtos_list
    }

pedidos = {}
pedidos_lock = threading.Lock()
prox_id = 1

gerar_chaves("principal")

# função de interação com o usuário pelo terminal
def interacao():
    global prox_id, produtos
    
    def publicar_interacao(event, conteudo):
        # conexão separada para a interação
        # evitar bloqueio de conexão por demora na interação
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        channel = connection.channel()
        channel.exchange_declare(exchange="direct_logs", exchange_type="direct")
        publish_event(publisher="principal", channel=channel, event=event, conteudo=conteudo)
        connection.close()
    
    while True:
        print("\n========================")
        print("Selecione uma opção:")
        print("1 - Visualizar produtos")
        print("2 - Realizar pedido")
        print("3 - Excluir pedido")
        print("4 - Consultar pedidos")
        print("5 - Sair")
        print("========================\n")
        
        try:
            opcao = int(input(' '))
        except ValueError:
            print("Insira uma opção válida")
            continue
        
        match opcao:
            case 1:
                print("\n=== Catálogo de produtos ===")
                for i, produto in enumerate(produtos):
                    print(f"{i + 1} - {produto.get_nome()} ({produto.get_categoria()})  R${produto.get_preco()}")
            case 2:
                # fazer o pedido
                print("\n=== Realizar pedido ===")
                for produto in produtos:
                    print(f"{produto.get_id()} - {produto.get_nome()} ({produto.get_categoria()})  R${produto.get_preco()}")
                
                fazer_pedido = 1
                pedido_produtos = []
                quantidade_produtos = []

                while fazer_pedido:
                    try:
                        produto_escolhido = int(input("\nInsira o número do produto: ")) - 1
                        quantidade = int(input("Quantidade: "))
                    except ValueError:
                        print("Valor inválido")
                        continue
                    
                    if produto_escolhido < 0 or produto_escolhido >= len(produtos):
                        print("Produto inválido.")
                        continue
                    if quantidade < 0:
                        print("Quantidade inválida.")
                        continue
                    
                    pedido_produtos.append(produtos[produto_escolhido])
                    quantidade_produtos.append(quantidade)
                    
                    try:
                        fazer_pedido = int(input("\nComprar mais algum produto? (1 - Sim ; 0 - Não) "))
                    except ValueError:
                        fazer_pedido = 0

                pedido_id = prox_id
                prox_id += 1
                
                novo_pedido = {
                    "pedido_id": pedido_id,
                    "produtos": [
                        {
                            "nome": produto.get_nome(),
                            "quantidade": quantidade,
                            "preco": produto.get_preco()
                        } for produto, quantidade in zip(pedido_produtos, quantidade_produtos)
                    ],
                    "status": "pedido criado"
                }
                
                with pedidos_lock:
                    pedidos[pedido_id] = novo_pedido
                
                publicar_interacao(event=pedido.criado, conteudo=novo_pedido)
                print(f"\nPedido {pedido_id} criado!")

            case 3:
                print("\n=== Excluir pedido ===")
                try:
                    pedido_id = int(input("Insira o número do pedido: "))
                except ValueError:
                    print("Número inválido")
                    continue
                
                if pedido_id not in pedidos:
                    print("Pedido não encontrado.")
                    continue
                
                with pedidos_lock:
                    if "excluído" in pedidos[pedido_id]["status"]:
                        print(f"\nPedido {pedido_id} já está excluído!")
                        continue
                    pedidos[pedido_id]["status"] = "excluído"
                
                publicar_interacao(event=pedido.excluido, conteudo=pedidos[pedido_id])
                print(f"\nPedido {pedido_id} excluído!")
            
            case 4:
                print("\n=== Status de pedidos ===")
                with pedidos_lock:
                    if not pedidos:
                        print("Nenhum pedido registrado!")
                        continue

                    for pedido_id, dados in pedidos.items():
                        print(f"\nPedido {pedido_id} | Status: {dados['status']}")
                        for p in dados["produtos"]:
                            print(f"  - {p['nome']} ({p['quantidade']})")
            case 5:
                print("Encerrando...")
                break
            case _:
                print("Opção inválida")


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
