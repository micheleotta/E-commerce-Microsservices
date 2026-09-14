#!/usr/bin/env python
import pika
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from produtos import produtos
from microsservicos import pedido, estoque, receive_event, publish_event

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
    channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=f'{evento}')

quantidades_estoque = [5, 50, 20, 10, 10]
estoque_produtos = {produto.get_nome(): quantidade for produto, quantidade in zip(produtos, quantidades_estoque)}

def callback(ch, method, properties, body):
    valida, conteudo = receive_event(method, properties, body)
    evento = method.routing_key
    
    # processar evento somente se assinatura for válida!
    if valida:
        # se pedido.criado -> verificar disponibilidade
        pedido_id = conteudo['pedido_id']
        if evento == pedido.criado:
            for produto_pedido in conteudo['produtos']:
                nome = produto_pedido['nome']
                quantidade = produto_pedido['quantidade']
                
                if estoque_produtos[nome] < quantidade:
                    # se produto não disponível -> estoque.indisponivel
                    publish_event(publisher="estoque", channel=ch, event=estoque.indisponivel, conteudo=conteudo)
                    print(f"\nPedido {pedido_id} criado -> estoque indisponível de {nome} (solicitado = {quantidade}, no estoque = {estoque_produtos[nome]})")
                    return
            
            # caso todos os produtos estejam disponíveis
            # realizar reserva/baixa estoque -> pedido.estoque_ok
            print(f"\nPedido criado {pedido_id} -> estoque ok!\nReservando: ")
            for produto_pedido in conteudo['produtos']:
                nome = produto_pedido['nome']
                quantidade = produto_pedido['quantidade']
                
                antes = estoque_produtos[nome]
                estoque_produtos[nome] -= quantidade
                print(f"- {nome} = {antes} -> {estoque_produtos[nome]}")
            publish_event(publisher="estoque", channel=ch, event=pedido.estoque_ok, conteudo=conteudo)
        
        # se pedido.excluido -> devolver ao estoque produtos reservados
        elif evento == pedido.excluido:
            # se excluido por estoque indisponivel, não realizou reserva dos produtos
            if conteudo["status"] != "excluído - estoque indisponível":
                print(f"\nPedido excluido {pedido_id} -> estoque devolvido")
                for produto_reservado in conteudo['produtos']:
                    nome = produto_reservado['nome']
                    quantidade = produto_reservado['quantidade']
                    antes = estoque_produtos[nome]
                    estoque_produtos[nome] += quantidade
                    print(f"- {nome} = {antes} -> {estoque_produtos[nome]}")

    else:
        print(f"Assinatura inválida, evento {evento} descartado!")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    print("Microsserviço de estoque iniciado!")
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()