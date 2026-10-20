"""
Aplicação web externa simples que simula um provedor de pagamentos
"""

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import uvicorn
import requests
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Mock de Pagamento")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=f"{BASE_DIR}/templates")

# Página de erro genérica para lidar com exceções HTTP
@app.exception_handler(StarletteHTTPException)
async def tratar_http_exception(req: Request, exc: StarletteHTTPException):
    titulos = {
        400: "Requisição inválida",
        401: "Não autorizado",
        403: "Acesso negado",
        404: "Página não encontrada",
        410: "Página indisponível",
        422: "Dados inválidos",
        500: "Erro interno do servidor",
    }

    return templates.TemplateResponse(
        request=req,
        name="erro.html",
        context={
            "status_code": exc.status_code,
            "titulo": titulos.get(exc.status_code, "Ocorreu um erro"),
            "mensagem": str(exc.detail),
        },
        status_code=exc.status_code,
        headers=exc.headers,
    )

pagamentos = {}

# Processa a solicitação de cobrança do MS Pagamento via REST
class SolicitacaoPagamento(BaseModel):
    pedido_id: int
    produtos: list
    valor: float
    callback_url: str

@app.post("/api/pagamento")
def iniciar_pagamento(body: SolicitacaoPagamento):
    if not body.pedido_id:
        raise HTTPException(status_code=400, detail="Faltando ID do pedido")

    pagamentos[str(body.pedido_id)] = {
        "produtos": body.produtos,
        "valor": body.valor,
        "callback_url": body.callback_url
    }

    pagamento_url = f"http://localhost:8100/checkout/{body.pedido_id}"
    return { "pedido_id": body.pedido_id, "pagamento_url": pagamento_url }

@app.get("/checkout/{pedido_id}", response_class=HTMLResponse)
def pagina_checkout(req: Request, pedido_id: str):
    pagamento = pagamentos.get(pedido_id)

    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    
    if pagamento.get("finalizado", False):
        raise HTTPException(status_code=410, detail="Este checkout já foi finalizado.")
    
    return templates.TemplateResponse(request=req, name="checkout.html", context={
        "pedido_id": pedido_id,
        "valor": pagamento["valor"]
    })

# Abre uma página no navegador onde o usuário clica nos botões "Pagamento Aprovado" ou "Pagamento Recusado".
# Quando o usuário clicar, faz uma chamada HTTP POST (Webhook) para a URL informada pelo MS Pagamento.
@app.post("/pagamento/{pedido_id}", response_class=HTMLResponse)
def processar_pagamento(req: Request, pedido_id: str, action: str = Form(...)):
    pagamento = pagamentos.get(pedido_id)

    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    if pagamento.get("finalizado", False):
        raise HTTPException(status_code=410, detail="Este pagamento já foi processado.")

    if action == "aprovar":
        status = "aprovado"
        aprovado = True
    else:
        status = "recusado"
        aprovado = False
    pagamentos[pedido_id]["finalizado"] = True

    try:
        response = requests.post(
            pagamento["callback_url"],
            json={
                "pedido_id": pedido_id,
                "produtos": pagamento["produtos"],
                "aprovado": aprovado
            },
            timeout=5
        )
        response.raise_for_status()
    
    except requests.RequestException:
        return HTMLResponse(f"""<h1 style="color: #CC0000;">Erro ao finalizar pagamento!</h1>""")
    
    return templates.TemplateResponse(request=req, name="finalizado.html", context={
        "status": status
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)