#!/usr/bin/env python
import pika
from microsservicos.microsservicos import *
from enum import Enum
import time
import random

promocao = Enum('promocao', 'categoria', categorias)

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo por topic
channel.exchange_declare(exchange='logs', exchange_type='topic')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# gerar e publicar promocoes aleatórias produtos
while True:
    produto = random.choice(produtos) # fazer
    desconto = random.randint(5, 50)
    categoria = produto.get_categoria()
    # channel publish
    
    time.sleep(3)