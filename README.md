# E-commerce Microsservices

Aplicação Web completa de um sistema distribuído de *e-commerce* baseado em microsserviços para gerenciamento de pedidos, estoque de produtos, pagamentos, entregas e notificações. Comunicação REST entre Frontend e API Gateway, notificações em tempo real via SSE, mensageria com RabbitMQ, integrações com APIs Externas (E-mail e Pagamento via Webhook) e uso de criptografia de Chave Assimétrica.

## Dependências
* Instalar o RabbitMQ
* `pip install -r requirements.txt`
* Obter `RESEND_API_KEY` e colocá-la em `.env`

## Para rodar:
RabbitMQ
* (Linux) `sudo systemctl start docker`
* `docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management`

Frontend -> acessar via `http://localhost:5500`
* (front-end) `python -m http.server 5500`

Backend
* `python microsservicos/principal/principal.py`
* `python microsservicos/estoque/estoque.py`
* `python microsservicos/pagamento/pagamento.py`
* `python microsservicos/entrega/entrega.py`
* `python microsservicos/promocoes/promocoes.py`
* `python pagamento-mock/pagamento-mock.py`

## Exemplificação
<img width="726" height="601" alt="image" src="https://github.com/user-attachments/assets/031b0206-9330-4db1-b035-e0138da18efb" />
