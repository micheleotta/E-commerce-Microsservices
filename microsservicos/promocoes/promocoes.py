#!/usr/bin/env python
import pika
import time
import random
import sys
import os
import threading
from dotenv import load_dotenv
import resend
from resend.exceptions import ResendError
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from produtos import produtos
from shared import interesse, receive_event, gerar_chaves

promocoes = {
    'doce': ['michfacul@gmail.com'],
    'salgado': ['michfacul@gmail.com'],
    'pao': ['michfacul@gmail.com']
    } # arrumar persistência dps

load_dotenv()
resend.api_key = os.environ["RESEND_API_KEY"] # obter chave API do arquivo .env


def send_mail(receiver, categoria, produto, desconto):
    params: resend.Emails.SendParams = {
    "from": "Acme <onboarding@resend.dev>",
    "to": [receiver],
    "subject": f"Promoção Especial em {categoria}!",
    "html": f"<strong>{produto} está com {desconto}% de desconto!</strong>",
    }

    try:
        email = resend.Emails.send(params)
        print(email)
    except ResendError as error:
        print(error)


def gerar_promocoes():
    while True:
        # gerar e publicar promocoes aleatórias de produtos
        produto = random.choice(produtos)
        nome = produto.get_nome()
        categoria = produto.get_categoria()
        desconto = random.randint(5, 50)

        for email in promocoes.get(categoria, []):
            send_mail(receiver=email, categoria=categoria, produto=nome, desconto=desconto)
        
        print(f"[{categoria}] Desconto {desconto}% em {nome}")
        time.sleep(30)


def callback(ch, method, properties, body):
    valida, conteudo = receive_event(consumer="promocoes", properties=properties, conteudo=body)
    evento = method.routing_key
    
    # processar evento somente se assinatura for válida!
    if valida:
        # identifica os interesses e e-mails dos consumidores cadastrados
        categoria = conteudo['categoria']
        email = conteudo['email']
        promocoes[categoria].append(email)
    else:
        print(f"Assinatura inválida, evento {evento} descartado!")


def consume():
    # conectar
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # tipo Direct
    channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
    result = channel.queue_declare(queue='promocoes', exclusive=True)
    queue_name = result.method.queue

    # consome o evento interesse.promocao
    channel.queue_bind(exchange='direct_logs', queue=queue_name, routing_key=interesse.promocao)
    
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    try:
        gerar_chaves("promocoes")
        print("Microsserviço de promocoes iniciado!")
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

thread_rabbit = threading.Thread(target=consume, daemon=True)
thread_rabbit.start()

time.sleep(20)
gerar_promocoes()