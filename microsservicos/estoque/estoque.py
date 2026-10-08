#!/usr/bin/env python
import pika
import sys
import os
from fastapi import FastAPI
import threading
import uvicorn
import bd.bakery_bd as bd # persiste os dados dos produtos em estoque
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import pedido, estoque, receive_event, publish_event, gerar_chaves


def consume():
    # conectar
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # tipo Direct
    channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
    result = channel.queue_declare(queue='estoque', exclusive=True)
    queue_name = result.method.queue

    # eventos que consome
    eventos = [pedido.criado, pedido.excluido]
    for evento in eventos:
        # subscribing, novo binding para cada evento de interesse
        channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=evento)
    
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    try:
        gerar_chaves("estoque")
        print("Microsserviço de estoque iniciado!")
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


def callback(ch, method, properties, body):
    valida, conteudo = receive_event(consumer="estoque", properties=properties, conteudo=body)
    evento = method.routing_key
    
    # processar evento somente se assinatura for válida!
    if valida:
        # se pedido.criado -> verificar disponibilidade
        pedido_id = conteudo['pedido_id']
        if evento == pedido.criado:
            for produto_pedido in conteudo['produtos']:
                id_produto = produto_pedido['id_produto']
                nome = produto_pedido['nome']
                quantidade = produto_pedido['quantidade']
                estoque_produto = bd.get_estoque({'id_produto': id_produto})[0]
                
                if estoque_produto < quantidade:
                    # se produto não disponível -> estoque.indisponivel
                    publish_event(publisher="estoque", channel=ch, event=estoque.indisponivel, conteudo=conteudo)
                    print(f"\nPedido criado {pedido_id} -> estoque indisponível de {nome} (solicitado = {quantidade}, no estoque = {estoque_produto})")
                    return
            
            # caso todos os produtos estejam disponíveis
            # realizar reserva/baixa estoque -> pedido.estoque_ok
            print(f"\nPedido criado {pedido_id} -> estoque ok!\nReservando: ")
            for produto_pedido in conteudo['produtos']:
                id_produto = produto_pedido['id_produto']
                nome = produto_pedido['nome']
                quantidade = produto_pedido['quantidade']
                
                antes = bd.get_estoque({'id_produto': id_produto})[0]
                bd.reservar_produto({'id_produto': id_produto, 'quantidade': quantidade})
                print(f"- {nome} = {antes} -> {bd.get_estoque({'id_produto': id_produto})[0]}")
            publish_event(publisher="estoque", channel=ch, event=pedido.estoque_ok, conteudo=conteudo)
        
        # se pedido.excluido -> devolver ao estoque produtos reservados
        elif evento == pedido.excluido:
            # se excluido por estoque indisponivel, não realizou reserva dos produtos
            if conteudo["status"] != "excluído - estoque indisponível":
                print(f"\nPedido excluido {pedido_id} -> estoque devolvido")
                for produto_reservado in conteudo['produtos']:
                    id_produto = produto_reservado['id_produto']
                    nome = produto_reservado['nome']
                    quantidade = produto_reservado['quantidade']
                    
                    antes = bd.get_estoque({'id_produto': id_produto})[0]
                    bd.devolver_produto({'id_produto': id_produto, 'quantidade': quantidade})
                    print(f"- {nome} = {antes} -> {bd.get_estoque({'id_produto': id_produto})[0]}")
    else:
        print(f"Assinatura inválida, evento {evento} descartado!")


# expõe um endpoint para o MS principal consultar produtos disponíveis!
app = FastAPI(title="Microsserviço de Estoque")
@app.get("/produtos")
def consultar_produtos():
    produtos = bd.get_produtos()

    produtos_disponiveis = [
        {
            "id_produto": produto[0],
            "nome": produto[1],
            "categoria": produto[2],
            "preco": produto[3],
            "estoque": produto[4]
        }
        for produto in produtos
    ]

    return {
        "total": len(produtos_disponiveis),
        "produtos": produtos_disponiveis
    }

@app.get("/categorias")
def consultar_categorias():
    categorias = bd.get_categorias()
    return categorias


if __name__ == "__main__":
    thread_rabbit = threading.Thread(target=consume, daemon=True)
    thread_rabbit.start()
    uvicorn.run(app, host="0.0.0.0", port=8001)
