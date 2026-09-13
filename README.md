# E-commerce Microsservices

*Backend* de um sistema distribuído de *e-commerce* baseado em microsserviços para gerenciamento de pedidos, estoque de produtos, pagamentos, entregas e notificações. Sistema com arquitetura orientada a eventos (Event-Driven Architecture), através de um broker RabbitMQ.

## Dependências
* Instalar o [RabbitMQ](https://www.rabbitmq.com/tutorials) `docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management`
* `pip install pika`
* `pip install pycryptodome`
