#!/usr/bin/env python
import pika
from microsservicos.microsservicos import *
from enum import Enum

promocao = Enum('promocao', 'categoria', ['A', 'B', 'C'])

# conectar
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# tipo por topic
channel.exchange_declare(exchange='logs', exchange_type='topic')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# gerar e publicar promocoes aleatórias produtos
# NÃO CONSOME NADA
