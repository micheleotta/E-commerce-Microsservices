#!/usr/bin/env python
import pika
import sys
import os
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from produtos import produtos
from microsservicos import pagamento, pedido, estoque, receive_event, publish_event

pedidos = {}
pedidos_lock = threading.Lock()
prox_id = 1

# função de interação com o usuário
def interacao():
    global prox_id, produtos
    
    # conexão separada para a interação
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange="direct_logs", exchange_type="direct")
    
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
                
                publish_event('principal', channel, f'{pedido.criado}', novo_pedido)
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
                    pedidos[pedido_id]["status"] = "excluído"
                
                publish_event('principal', channel, f'{pedido.excluido}', pedidos[pedido_id])
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
                connection.close()
                break
            case _:
                print("Opção inválida")


def callback(ch, method, properties, body):
    valida, conteudo = receive_event(method, properties, body)
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
                status = "excluído"
                publish_event('principal', ch, f'{pedido.excluido}', pedidos[pedido_id])
            pedidos[pedido_id]["status"] = status
            
        print(f"Pedido {pedido_id} atualizado -> Status: {status}")
    else:
        print(f"Assinatura inválida, evento {evento} descartado!")


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
        channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=f'{evento}')
    
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


thread_rabbit = threading.Thread(target=consume, daemon=True)
thread_rabbit.start()
interacao()