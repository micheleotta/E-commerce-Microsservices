const baseUrl = 'http://localhost:8000';

class Carrinho {
    constructor() {
        this.produtoQtd = {};
    }

    addProduto(produtoId) {
        if (produtos[produtoId]) {
            this.produtoQtd[produtoId] = (this.produtoQtd[produtoId] || 0) + 1;
        } else {
            console.error(`Produto com ID ${produtoId} não encontrado.`);
        }

        console.log(`Produto com ID ${produtoId} adicionado ao carrinho.`);
    }

    removeProduto(produtoId) {
        this.produtoQtd[produtoId] = (this.produtoQtd[produtoId] || 0) - 1;
        if (this.produtoQtd[produtoId] <= 0)
            delete this.produtoQtd[produtoId];

        console.log(`Produto com ID ${produtoId} removido do carrinho.`);
    }
}

produtos = {};
carrinho = new Carrinho();

function removeProduto(produtoId) {
    carrinho.removeProduto(produtoId);
}

function addProduto(produtoId) {
    carrinho.addProduto(produtoId);
}

function fazerPedido() {
    if (Object.keys(carrinho.produtoQtd).length === 0) {
        alert('O carrinho está vazio. Adicione produtos antes de fazer o pedido.');
        return;
    }

    var url = `${baseUrl}/pedido`;
    var headers = new Headers();
    headers.append('Content-Type', 'application/json');

    var data = {
        produtos: Object.entries(carrinho.produtoQtd).map(([id, quantidade]) => {
            return { ...produtos[id], quantidade: quantidade };
        })
    };

    fetch(url, { method: 'POST', headers: headers, body: JSON.stringify(data) })
        .then(response => response.json())
        .then(data => {
            console.log(data);
        })
        .catch(error => {
            console.error('Erro ao buscar produtos:', error);
        });
}

function displayProdutos(produtos) {
    if (!Array.isArray(produtos)) {
        console.error('O parâmetro "produtos" deve ser um array.');
        return;
    }
    
    var produtosContainer = document.getElementById('product-list');
    produtosContainer.innerHTML = '';
    
    produtos.forEach(function(produto) {
        produtosContainer.innerHTML += `
            <div class="produto col-md-4">
                <div class="produto-card">
                    <div class="produto-info">
                        <h3>${produto.nome}</h3>
                        <p>R$${produto.preco.toFixed(2)}</p>
                    </div>
                    <div class="produto-footer">
                        <button onclick="removeProduto(${produto.id_produto})" class="btn-icon btn-remove">
                            <span class="material-symbols-outlined">remove</span>
                        </button>
                        <button onclick="addProduto(${produto.id_produto})" class="btn-icon btn-add">
                            <span class="material-symbols-outlined">add</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
}

function getProdutos() {
    var url = `${baseUrl}/produtos`;
    var headers = new Headers();

    fetch(url, { method: 'GET', headers: headers })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            var list = data?.produtos || [];
            displayProdutos(list);

            list.forEach(function(produto) {
                produtos[produto.id_produto] = produto;
            });
        })
        .catch(error => {
            console.error('Erro ao buscar produtos:', error);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    getProdutos();
});