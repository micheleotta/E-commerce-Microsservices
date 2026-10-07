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
                        <button class="btn btn-remove">
                            <span class="material-symbols-outlined">remove</span>
                        </button>
                        <button class="btn btn-add">
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
            displayProdutos(data?.produtos);
        })
        .catch(error => {
            console.error('Erro ao buscar produtos:', error);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    getProdutos();
});