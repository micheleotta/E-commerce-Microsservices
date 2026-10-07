class Carrinho {
    constructor() {
        this.produtos = [];
    }

    addProduto(produtoId) {
        const produto = produtos.find(produto => produto.id_produto === produtoId);
        if (produto) {
            this.produtos.push(produto);
        } else {
            console.error(`Produto com ID ${produtoId} não encontrado.`);
        }

        console.log(`Produto com ID ${produtoId} adicionado ao carrinho.`);
    }

    removeProduto(produtoId) {
        this.produtos = this.produtos.filter(produto => produto.id_produto !== produtoId);
        console.log(`Produto com ID ${produtoId} removido do carrinho.`);
    }
}

produtos = [];
carrinho = new Carrinho();

function removeProduto(produtoId) {
    carrinho.removeProduto(produtoId);
}

function addProduto(produtoId) {
    carrinho.addProduto(produtoId);
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
                        <button onclick="removeProduto(${produto.id_produto})" class="btn btn-remove">
                            <span class="material-symbols-outlined">remove</span>
                        </button>
                        <button onclick="addProduto(${produto.id_produto})" class="btn btn-add">
                            <span class="material-symbols-outlined">add</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
}

function getProdutos() {
    var url = 'http://localhost:8000/produtos';
    var headers = new Headers();

    fetch(url, { method: 'GET', headers: headers })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            produtos = data?.produtos || [];
            displayProdutos(produtos);
        })
        .catch(error => {
            console.error('Erro ao buscar produtos:', error);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    getProdutos();
});