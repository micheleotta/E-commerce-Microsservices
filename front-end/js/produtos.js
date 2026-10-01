function getProdutos() {
    var url = 'http://localhost:8000/produtos';
    var headers = new Headers();

    fetch(url, { method: 'GET', headers: headers })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            // Aqui você pode manipular os dados recebidos da API
        })
        .catch(error => {
            console.error('Erro ao buscar produtos:', error);
        });
}