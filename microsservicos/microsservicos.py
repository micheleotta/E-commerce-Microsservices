from enum import Enum
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

from produtos import *

# Definir tipos de eventos
pedido = Enum('pedido', ['criado', 'enviado', 'estoque_ok', 'excluido'])
estoque = Enum('estoque', ['indisponivel'])
pagamento = Enum('pagamento', ['aprovado', 'recusado'])

# Publicar um evento
def publish_event(publisher, channel, event, conteudo):
    # gerar hash do conteudo do evento
    key = RSA.import_key(open(f'{publisher}/private_key.der').read()) # MUDAR***
    hash = SHA256.new(conteudo)
    
    # assinar o evento utilizando criptografia assimétrica
    assinatura = pkcs1_15.new(key).sign(hash)
    
    # incluir a assinatura digital no campo Signature do envelope do evento.
    channel.basic_publish(exchange="",
        routing_key=event,
        body=conteudo,
        signature=assinatura)

# Verificar recebimento de evento
def receive_event(publisher, conteudo, assinatura):
    # obter chave publica do microsserviço produtor
    key = RSA.import_key(open(f'{publisher}/public_key.der').read())
    hash = SHA256.new(conteudo)
    
    # verificar assinatura digital do evento
    
    # confirmar a autenticidade e a integridade da mensagem
    try:
        pkcs1_15.new(key).verify(hash, assinatura)
        return True
    except (ValueError, TypeError):
        return False