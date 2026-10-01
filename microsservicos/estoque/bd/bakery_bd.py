import sqlite3
import os

dir = os.path.dirname(os.path.abspath(__file__))
caminho = os.path.join(dir, "bakery.db")

# conecta ao banco de dados (cria se ele não existir)
connection = sqlite3.connect(caminho)
cursor = connection.cursor()

# cria uma tabela
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS bakery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    categoria TEXT NOT NULL,
    preco DECIMAL (10, 2),
    estoque INTEGER )
    """
)
connection.commit()

# insere registros
cursor.execute("SELECT COUNT(*) FROM bakery")
count = cursor.fetchone()[0]
if count == 0:
    produtos = [
        ('Carolina', 'doce', 5.0, 25),
        ('Donut', 'doce', 12.0, 50),
        ('Coxinha', 'salgado', 2.0, 20),
        ('Bisnaguinha', 'pao', 30.0, 10),
        ('Croissant', 'pao', 20.0, 10)
    ]
    
    cursor.executemany(
        """
        INSERT INTO bakery (nome, categoria, preco, estoque)
        VALUES (?, ?, ?, ?)
        """, produtos
        )
    
    connection.commit()
connection.close()

# funções auxiliares
def get_connection():
    return sqlite3.connect(caminho)

# produtos
def get_produtos():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM bakery")
        produtos = cursor.fetchall()
        return produtos
    finally:
        connection.close()

# estoque
def get_estoque(produto):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        id_produto = produto["id_produto"]
        cursor.execute("SELECT estoque FROM bakery WHERE id = ?", (id_produto,))
        estoque = cursor.fetchone()
        return estoque
    finally:
        connection.close()

def devolver_produto(produto):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        id_produto = produto["id_produto"]
        quantidade = produto["quantidade"]
        cursor.execute("UPDATE bakery SET estoque = estoque + ? WHERE id = ?", (quantidade, id_produto))
        connection.commit()
    finally:
        connection.close()

def reservar_produto(produto):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        id_produto = produto["id_produto"]
        quantidade = produto["quantidade"]
        cursor.execute("UPDATE bakery SET estoque = estoque - ? WHERE id = ?", (quantidade, id_produto))
        connection.commit()
    finally:
        connection.close()