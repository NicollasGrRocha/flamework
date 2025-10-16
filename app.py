from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime

# --- Configuração do Banco de Dados MySQL ---
DB_CONFIG = {
    # ATENÇÃO: Substitua pelos seus dados reais do MySQL
    'user': 'root',
    'password': '218101809Luiz.',
    'host': 'localhost',
    'database': 'db_projeto'# Alterei o nome do DB para refletir o projeto
}

app = Flask(__name__)
CORS(app)  # Adiciona CORS para permitir o frontend


# Função de conexão com o banco
def get_connection():
    """Cria e retorna uma nova conexão com o banco de dados MySQL."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Erro de acesso ao MySQL: verifique usuário ou senha.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"O banco de dados '{DB_CONFIG['database']}' não existe.")
        else:
            print(f"Erro ao conectar ao MySQL: {err}")
        return None


# Criar tabelas
def init_db():
    con = get_connection()
    if con is None:
        print("Falha ao inicializar o DB. Verifique a conexão.")
        return

    cursor = con.cursor()
    try:
        # 1. Cria a tabela de produtos (Se não existir)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                IdProduto INT PRIMARY KEY AUTO_INCREMENT,
                NomeProduto VARCHAR(255) NOT NULL,
                Preco DECIMAL(10, 2) NOT NULL,
                Quantidade INT NOT NULL
            )
        """)

        # 2. Cria a tabela de compras (histórico)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                IdCompra INT PRIMARY KEY AUTO_INCREMENT,
                DataCompra DATETIME NOT NULL,
                Total DECIMAL(10,2) NOT NULL
            )
        """)

        # 3. Cria a tabela de itens da compra
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_compra (
                IdItem INT PRIMARY KEY AUTO_INCREMENT,
                IdCompra INT NOT NULL,
                IdProduto INT NOT NULL,
                NomeProduto VARCHAR(255) NOT NULL,
                Preco DECIMAL(10,2) NOT NULL,
                Quantidade INT NOT NULL,
                Subtotal DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (IdCompra) REFERENCES compras(IdCompra),
                FOREIGN KEY (IdProduto) REFERENCES produtos(IdProduto)
            )
        """)

        # 2. Verifica se a tabela está vazia
        cursor.execute("SELECT COUNT(*) FROM produtos")
        count = cursor.fetchone()[0]

        if count == 0:
            # 3. Adiciona o produto padrão (SE A TABELA ESTIVER VAZIA)
            print("Adicionando produto padrão para testes...")
            cursor.execute(
                "INSERT INTO produtos (NomeProduto, Preco, Quantidade) VALUES (%s, %s, %s)",
                ("Pão de Forma Integral", 8.50, 100)
            )

        con.commit()
        print(f"Tabela 'produtos' verificada/criada com sucesso no MySQL. {count} produto(s) encontrado(s).")

    except mysql.connector.Error as err:
        print(f"Erro ao criar tabelas ou inserir dados no MySQL: {err}")
    finally:
        cursor.close()
        con.close()


init_db()


# No topo do seu app.py, certifique-se que o render_template está importado:
# from flask import Flask, render_template, request, jsonify
# ...

@app.route("/")
def index():
# Histórico de compras em memória (substitua por tabela no futuro)
    # CORRIGIDO: Agora, ele busca e renderiza o arquivo da pasta 'templates'
    return render_template("index.html")


# --- CRUD Produtos ---
@app.route("/api/products", methods=["GET"])
def list_products():
    con = get_connection()
    if con is None: return jsonify({"error": "Erro de conexão com o DB."}), 500

    # Em MySQL, usamos o cursor(dictionary=True) para obter resultados como dicionário
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()
    con.close()

    # O jsonify já recebe a lista de dicionários diretamente
    return jsonify(rows)


@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    con = get_connection()
    if con is None: return jsonify({"error": "Erro de conexão com o DB."}), 500

    cursor = con.cursor()
    # No MySQL, usamos %s como placeholder, e não o ? do SQLite
    query = "INSERT INTO produtos (NomeProduto, Preco, Quantidade) VALUES (%s, %s, %s)"
    values = (data["NomeProduto"], data["Preco"], data["Quantidade"])

    try:
        cursor.execute(query, values)
        con.commit()
        return jsonify({"message": "Produto adicionado com sucesso!", "IdProduto": cursor.lastrowid})
    except mysql.connector.Error as err:
        con.rollback()
        return jsonify({"error": f"Erro ao adicionar produto: {err}"}), 500
    finally:
        cursor.close()
        con.close()


@app.route("/api/products/<int:id>", methods=["PUT"])
def update_product(id):
    data = request.json
    con = get_connection()
    if con is None: return jsonify({"error": "Erro de conexão com o DB."}), 500

    cursor = con.cursor()
    query = "UPDATE produtos SET NomeProduto=%s, Preco=%s, Quantidade=%s WHERE IdProduto=%s"
    values = (data["NomeProduto"], data["Preco"], data["Quantidade"], id)

    try:
        cursor.execute(query, values)
        con.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Produto não encontrado ou nenhum dado alterado."}), 404
        return jsonify({"message": "Produto atualizado com sucesso!"})
    except mysql.connector.Error as err:
        con.rollback()
        return jsonify({"error": f"Erro ao atualizar produto: {err}"}), 500
    finally:
        cursor.close()
        con.close()


@app.route("/api/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    con = get_connection()
    if con is None: return jsonify({"error": "Erro de conexão com o DB."}), 500

    cursor = con.cursor()
    query = "DELETE FROM produtos WHERE IdProduto=%s"

    try:
        cursor.execute(query, (id,))
        con.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Produto não encontrado."}), 404
        return jsonify({"message": "Produto removido com sucesso!"})
    except mysql.connector.Error as err:
        con.rollback()
        return jsonify({"error": f"Erro ao remover produto: {err}"}), 500
    finally:
        cursor.close()
        con.close()


# --- Compra ---
@app.route("/api/purchase", methods=["POST"])
def purchase():
    data = request.json
    if 'cart' not in data or not isinstance(data['cart'], list):
        return jsonify({"error": "Dados inválidos: 'cart' é obrigatório e deve ser uma lista."}), 400

    con = get_connection()
    if con is None: return jsonify({"error": "Erro de conexão com o DB."}), 500

    cursor = con.cursor()
    total = 0
    items = []

    try:
        # Inicia a transação para garantir que o estoque só seja atualizado se a compra for bem-sucedida
        con.start_transaction()

        for item in data["cart"]:
            product_id = item.get("IdProduto")
            quantity = item.get("Quantidade")

            if not product_id or not quantity or quantity <= 0:
                con.rollback()
                return jsonify(
                    {"error": "Item do carrinho inválido (IdProduto e Quantidade > 0 são obrigatórios)."}), 400

            # 1. Busca o produto e bloqueia a linha (FOR UPDATE)
            cursor.execute("SELECT NomeProduto, Preco, Quantidade FROM produtos WHERE IdProduto=%s FOR UPDATE",
                           (product_id,))
            product = cursor.fetchone()

            if not product:
                con.rollback()
                return jsonify({"error": f"Produto com ID {product_id} não encontrado."}), 404

            # product é uma tupla: (NomeProduto, Preco, Quantidade)
            nome, preco, estoque = product

            if estoque < quantity:
                con.rollback()
                return jsonify({"error": f"Estoque insuficiente para {nome}! Disponível: {estoque}"}), 400

            # 2. Calcula subtotal
            # É melhor garantir que o cálculo seja feito com valores numéricos para evitar erros
            subtotal = float(preco) * quantity
            total += subtotal
            items.append({
                "IdProduto": product_id,
                "NomeProduto": nome,
                "Preco": float(preco),
                "Quantidade": quantity,
                "Subtotal": round(subtotal, 2)
            })

            # 3. Atualiza estoque
            cursor.execute("UPDATE produtos SET Quantidade = Quantidade - %s WHERE IdProduto=%s",
                           (quantity, product_id))

        # Se tudo ocorreu bem, confirma todas as mudanças
        con.commit()

        # Salva a compra no banco de dados (dentro da mesma transação)
        data_compra = datetime.now()
        cursor.execute(
            "INSERT INTO compras (DataCompra, Total) VALUES (%s, %s)",
            (data_compra, round(total, 2))
        )
        id_compra = cursor.lastrowid

        # Insere os itens da compra
        for item in items:
            if item.get("IdProduto") is None:
                con.rollback()
                return jsonify({"error": "IdProduto não pode ser nulo ao registrar item da compra."}), 400
            cursor.execute(
                "INSERT INTO itens_compra (IdCompra, IdProduto, NomeProduto, Preco, Quantidade, Subtotal) VALUES (%s, %s, %s, %s, %s, %s)",
                (id_compra, item["IdProduto"], item["NomeProduto"], item["Preco"], item["Quantidade"], item["Subtotal"])
            )
        con.commit()

    except mysql.connector.Error as err:
        con.rollback()
        return jsonify({"error": f"Erro na transação: {err}"}), 500
    finally:
        cursor.close()
        con.close()

    nota = {
        "itens": items,
        "total": round(total, 2),
        "data": data_compra.strftime("%d/%m/%Y %H:%M:%S")
    }
    return jsonify(nota)
# Rota para histórico de compras
@app.route("/api/history", methods=["GET"])
def get_history():
    con = get_connection()
    if con is None:
        return jsonify([])
    cursor = con.cursor(dictionary=True)
    # Busca as compras mais recentes primeiro
    cursor.execute("SELECT * FROM compras ORDER BY DataCompra DESC")
    compras = cursor.fetchall()
    historico = []
    for compra in compras:
        cursor.execute("SELECT NomeProduto, Preco, Quantidade, Subtotal FROM itens_compra WHERE IdCompra=%s", (compra["IdCompra"],))
        itens = cursor.fetchall()
        historico.append({
            "data": compra["DataCompra"].strftime("%d/%m/%Y %H:%M:%S"),
            "total": float(compra["Total"]),
            "itens": itens
        })
    cursor.close()
    con.close()
    return jsonify(historico)


if __name__ == "__main__":
    app.run(debug=True)