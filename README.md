# E-commerce Microsservices

*Backend* de um sistema distribuído de *e-commerce* baseado em microsserviços para gerenciamento de pedidos, estoque de produtos, pagamentos, entregas e notificações. Sistema com arquitetura orientada a eventos (*Event-Driven Architecture*), através de um broker RabbitMQ, e uso de criptografia de Chave Assimétrica

## Dependências
* Instalar o RabbitMQ
* `pip install pika`
* `pip install pycryptodome`

## Para rodar:
* `docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management`
* `python microsservicos/principal/principal.py`
* `python microsservicos/estoque/estoque.py`
* `python microsservicos/pagamento/pagamento.py`
* `python microsservicos/entrega/entrega.py`
* `python microsservicos/promocoes/promocoes.py`
* `python consumidor_C1.py`
* `python consumidor_C2.py`

## Exemplificação
<img width="1134" height="626" alt="image" src="https://github.com/user-attachments/assets/bb30c5be-b24e-4a6c-b90c-4661d1008e5b" />
