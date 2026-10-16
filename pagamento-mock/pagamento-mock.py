from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
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

pagamentos = {}

class SolicitacaoPagamento(BaseModel):
    pedido_id: int
    valor: float
    callback_url: str

@app.post("/api/pagamento")
def iniciar_pagamento(body: SolicitacaoPagamento):
    if not body.pedido_id:
        raise HTTPException(status_code=400, detail="Faltando ID do pedido")

    pagamentos[str(body.pedido_id)] = {
        "valor": body.valor,
        "callback_url": body.callback_url
    }

    pagamento_url = f"http://localhost:8100/checkout/{body.pedido_id}"
    return { "pagamento_url": pagamento_url }

@app.get("/checkout/{pedido_id}", response_class=HTMLResponse)
def pagina_checkout(req: Request, pedido_id: str):
    pagamento = pagamentos.get(pedido_id)

    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    
    return templates.TemplateResponse(request=req, name="checkout.html", context={
        "pedido_id": pedido_id,
        "valor": pagamento["valor"]
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)