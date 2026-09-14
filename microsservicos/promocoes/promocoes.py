#!/usr/bin/env python
import pika
import time
import random
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from produtos import produtos

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo por topic
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
result = channel.queue_declare(queue='promocoes', exclusive=True)
queue_name = result.method.queue

# gerar e publicar promocoes aleatórias de produtos
while True:
    produto = random.choice(produtos)
    nome = produto.get_nome()
    desconto = random.randint(5, 50)
    categoria = produto.get_categoria()
    conteudo = {
        "produto": nome,
        "categoria": categoria,
        "desconto": desconto
    }
    # channel publish
    channel.basic_publish(exchange='topic_logs', routing_key=f"promocao.categoria.{categoria}", body=json.dumps(conteudo))
    print(f"[promocao.categoria.{categoria}] Desconto {desconto}% em {nome}")
    time.sleep(5)