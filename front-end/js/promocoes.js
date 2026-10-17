var categorias = [];

function setCategorias(categorias) {
    var container = document.getElementById('categoria');
    container.innerHTML = '';

    categorias.forEach(categoria => {
        container.innerHTML += `<option value="${categoria}">${categoria}</option>`
    });
}

function getCategorias() {
    var url = `http://localhost:8000/categorias`;
    var headers = new Headers();

    fetch(url, { method: 'GET', headers: headers })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            categorias = data || [];
            setCategorias(categorias);
        })
        .catch(error => {
            console.error('Erro ao buscar categorias:', error);
        });
}

function informarInteresse() {
    var categoria = document.getElementById("categoria").value;
    var email = document.getElementById("email").value;

    var url = `http://localhost:8000/interesse`;
    var headers = new Headers();
    headers.append('Content-Type', 'application/json');

    fetch(url, { method: 'POST', headers: headers, body: JSON.stringify({ categoria, email }) })
        .then(response => response.json())
        .then(data => {
            console.log(data);
        })
        .catch(error => {
            console.error('Erro ao informar interesse:', error);
        });
}

function removerInteresse() {
    var categoria = document.getElementById("categoria").value;
    var email = document.getElementById("email").value;

    var url = `http://localhost:8000/interesse/${categoria}/${email}`;
    var headers = new Headers();

    fetch(url, { method: 'DELETE', headers: headers })
        .then(response => response.json())
        .then(data => {
            console.log(data);
        })
        .catch(error => {
            console.error('Erro ao remover interesse:', error);
        });
}

function abrirPromo() {
    var dialog = document.getElementById("promo-dialog");
    var email = localStorage.getItem("email");
    
    if (email)
        document.getElementById("email").value = email;

    dialog.showModal();
}

document.addEventListener('DOMContentLoaded', function() {
    getCategorias();
});