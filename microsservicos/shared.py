from enum import StrEnum
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import json
import pika
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# definir tipos de eventos
pedido = StrEnum('pedido', ['criado', 'enviado', 'estoque_ok', 'excluido'])
estoque = StrEnum('estoque', ['indisponivel'])
pagamento = StrEnum('pagamento', ['aprovado', 'recusado'])

microsservicos = {"principal", "estoque", "pagamento", "entrega"}

# gerar par de chaves RSA para microsservico
def gerar_chaves(publisher):
    # chave RSA de 2048 bits
    key = RSA.generate(2048)
    
    # salvar chave privada no próprio dir
    with open(f'{BASE_DIR}/{publisher}/private_key.der', 'wb') as f:
        f.write(key.export_key(format='DER'))
    
    # salvar chave pública
    # os microsserviços devem possuir as chaves públicas de todos os demais microsserviços
    for microsservico in (microsservicos - {publisher}):
        with open(f'{BASE_DIR}/{microsservico}/{publisher}_public_key.der', 'wb') as f:
            f.write(key.publickey().export_key(format='DER'))
    
    print(f"[{publisher}] chaves geradas!")

# publicar um evento
def publish_event(publisher, channel, event, conteudo):
    body = json.dumps(conteudo).encode("utf-8")
    
    # gerar hash do conteudo do evento
    key = RSA.import_key(open(f'{BASE_DIR}/{publisher}/private_key.der', 'rb').read())
    hash_conteudo = SHA256.new(body)
    
    # assinar o evento utilizando criptografia assimétrica
    assinatura = pkcs1_15.new(key).sign(hash_conteudo)
    
    # incluir a assinatura digital no campo Signature do envelope do evento
    properties = pika.BasicProperties(
        headers={
            'publisher': publisher,
            'signature': assinatura
            })
    
    channel.basic_publish(exchange='direct_logs',
        routing_key=event,
        body=body,
        properties=properties)

# verificar recebimento de evento
def receive_event(consumer, properties, conteudo):
    headers = properties.headers or {}
    publisher = headers.get('publisher')
    assinatura = headers.get('signature')
    
    if publisher is None or assinatura is None:
        return False, None
    
    try:
        # obter chave publica do microsserviço produtor
        key = RSA.import_key(open(f'{BASE_DIR}/{consumer}/{publisher}_public_key.der', 'rb').read())
        
        # confirmar a autenticidade e a integridade da mensagem
        # verificar assinatura digital do evento
        hash_conteudo = SHA256.new(conteudo)
        pkcs1_15.new(key).verify(hash_conteudo, assinatura)
        
        body = json.loads(conteudo.decode("utf-8"))
        return True, body
    
    except (ValueError, TypeError, OSError):
        return False, None