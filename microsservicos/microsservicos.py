from enum import Enum
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import json
import pika
from produtos import *

# Definir tipos de eventos
pedido = Enum('pedido', ['criado', 'enviado', 'estoque_ok', 'excluido'])
estoque = Enum('estoque', ['indisponivel'])
pagamento = Enum('pagamento', ['aprovado', 'recusado'])

# Publicar um evento
def publish_event(publisher, channel, event, conteudo):
    # gerar hash do conteudo do evento
    # key = RSA.import_key(open(f'{publisher}/private_key.der').read()) # MUDAR***
    # hash = SHA256.new(conteudo)
    
    # assinar o evento utilizando criptografia assimétrica
    # assinatura = pkcs1_15.new(key).sign(hash)
    
    # incluir a assinatura digital no campo Signature do envelope do evento
    microsservico = pika.BasicProperties(headers={'publisher': publisher})
    channel.basic_publish(exchange='direct_logs',
        routing_key=event,
        body=json.dumps(conteudo),
        properties=microsservico)
        # signature=assinatura)

# Verificar recebimento de evento
def receive_event(method, properties, conteudo):
    assinatura = method.signature
    headers = properties.headers or {}
    publisher = headers.get('publisher')
    # obter chave publica do microsserviço produtor
    # key = RSA.import_key(open(f'{publisher}/public_key.der').read())
    # hash = SHA256.new(conteudo)
    
    # verificar assinatura digital do evento
    
    # confirmar a autenticidade e a integridade da mensagem
    # try:
        #pkcs1_15.new(key).verify(hash, assinatura)
        #return True
    #except (ValueError, TypeError):
        #return False
    body = json.loads(conteudo)
    return True, body # alterar depois com a parte de criptografia