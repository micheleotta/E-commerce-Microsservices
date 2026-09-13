#!/usr/bin/env python
import pika
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from produtos import produtos
from microsservicos import pagamento, pedido, estoque, receive_event, publish_event

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
                
                prod = next((p for p in produtos if p.nome == nome), None)
                if not prod.verificar_estoque(quantidade):
                    # se produto não disponível -> estoque.indisponivel
                    publish_event(publisher="estoque", channel=ch, event=estoque.indisponivel, conteudo=conteudo)
                    print(f"\nPedido {pedido_id} criado -> estoque indisponível de {nome} (solicitado = {quantidade}, no estoque = {prod.get_estoque()})")
                    return
            
            # caso todos os produtos estejam disponíveis
            # realizar reserva/baixa estoque -> pedido.estoque_ok
            print(f"\nPedido criado {pedido_id} -> estoque ok!\nReservando: ")
            for produto_pedido in conteudo['produtos']:
                nome = produto_pedido['nome']
                quantidade = produto_pedido['quantidade']
                
                prod = next((p for p in produtos if p.nome == nome), None)
                antes = prod.get_estoque()
                prod.retirar_estoque(quantidade)
                print(f"- {nome} = {antes} -> {prod.get_estoque()}")
            publish_event(publisher="estoque", channel=ch, event=pedido.estoque_ok, conteudo=conteudo)
        
        # se pedido.excluido -> devolver ao estoque produtos reservados
        elif evento == pedido.excluido:
            # se excluido por estoque indisponivel, não realizou reserva dos produtos
            if not conteudo["status"] == "excluído - estoque indisponível":
                print(f"\nPedido excluido {pedido_id} -> estoque devolvido")
                for produto_reservado in conteudo['produtos']:
                    nome = produto_reservado['nome']
                    quantidade = produto_reservado['quantidade']
                    prod = next((p for p in produtos if p.nome == nome), None)
                    antes = prod.get_estoque()
                    prod.devolver_estoque(quantidade)
                    print(f"- {nome} = {antes} -> {prod.get_estoque()}")

    else:
        print(f"Assinatura inválida, evento {evento} descartado!")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
try:
    print("Microsserviço de estoque iniciado!")
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()