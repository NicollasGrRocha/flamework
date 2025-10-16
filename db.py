import sqlite3

DB_NAME = "supermercado.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    con = get_connection()
    cur = con.cursor()

    # Criar tabelas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        IdCategoria INTEGER PRIMARY KEY AUTOINCREMENT,
        NomeCategoria TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        IdProduto INTEGER PRIMARY KEY AUTOINCREMENT,
        NomeProduto TEXT NOT NULL,
        Preco REAL NOT NULL,
        Quantidade INTEGER NOT NULL,
        IdCategoria INTEGER,
        FOREIGN KEY (IdCategoria) REFERENCES categorias(IdCategoria)
    )
    """)

    # Inserir categorias iniciais
    cur.execute("INSERT OR IGNORE INTO categorias (IdCategoria, NomeCategoria) VALUES (1, 'Alimentos')")
    cur.execute("INSERT OR IGNORE INTO categorias (IdCategoria, NomeCategoria) VALUES (2, 'Bebidas')")

    con.commit()
    con.close()
