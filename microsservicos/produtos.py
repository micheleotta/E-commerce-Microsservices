class Produto:
    prox_id = 1
    
    def __init__(self, nome, categoria, preco):
        self.id = Produto.prox_id
        self.nome = nome
        self.categoria = categoria
        self.preco = preco
        
        Produto.prox_id += 1
    
    def get_id(self):
        return self.id
        
    def get_nome(self):
        return self.nome
    
    def get_categoria(self):
        return self.categoria
    
    def get_preco(self):
        return self.preco

categorias = ['doce', 'salgado', 'pao']

produtos = [
    Produto('Carolina', 'doce', 5.0),
    Produto('Donut', 'doce', 12.0),
    Produto('Coxinha', 'salgado', 2.0),
    Produto('Bisnaguinha', 'pao', 30.0),
    Produto('Croissant', 'pao', 20.0)
]