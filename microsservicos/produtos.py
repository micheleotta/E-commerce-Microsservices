class Produto:
    prox_id = 1
    
    def __init__(self, nome, categoria, preco, estoque, desconto = 0):
        self.id = Produto.prox_id
        self.nome = nome
        self.categoria = categoria
        self.preco = preco
        self.estoque = estoque
        self.desconto = desconto
        
        Produto.prox_id += 1
    
    def get_id(self):
        return self.id
        
    def get_nome(self):
        return self.nome
    
    def get_categoria(self):
        return self.categoria
    
    def set_desconto(self, desconto):
        self.desconto = desconto
    
    def get_estoque(self):
        return self.estoque
    
    def verificar_estoque(self, qtd = 1):
        return self.estoque >= qtd

    def retirar_estoque(self, qtd = 1):
        if self.verificar_estoque(qtd):
            self.estoque -= qtd
    
    def devolver_estoque(self, qtd):
        self.estoque += qtd
    
    def get_preco(self):
        return self.preco * (1 - self.desconto)

categorias = ['doce', 'salgado', 'pao']

produtos = [
    Produto('Donut', 'doce', 12.0, 5),
    Produto('Carolina', 'doce', 5.0, 50),
    Produto('Coxinha', 'salgado', 2.0, 20),
    Produto('Croissant', 'pao', 20.0, 10),
    Produto('Bisnaguinha', 'pao', 30.0, 10)
]