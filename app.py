from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import mysql.connector
import bcrypt
import re
from mysql.connector import errorcode
from datetime import datetime


DB_CONFIG = {
    'user': 'root',
    'password': '218101809Luiz.',
    'host': 'localhost',
    'database': 'db_projeto'
}

app = Flask(__name__)
CORS(app)
app.secret_key = 'sua_chave_secreta_aqui'



def requer_login(f):
    def decorador(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorador.__name__ = f.__name__
    return decorador



def requer_admin(f):
    def decorador(*args, **kwargs):
        if 'usuario_email' not in session or session['usuario_email'] != 'admin@gmail.com':
            return jsonify({"error": "Acesso negado: apenas o administrador pode realizar esta ação."}), 403
        return f(*args, **kwargs)
    decorador.__name__ = f.__name__
    return decorador


# --- Função de conexão ---
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:

        if err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"O banco de dados '{DB_CONFIG['database']}' não existe. Tentando criar...")
            try:

                cfg = DB_CONFIG.copy()
                cfg.pop('database', None)
                tmp_conn = mysql.connector.connect(**cfg)
                tmp_cursor = tmp_conn.cursor()
                tmp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}`")
                tmp_conn.commit()
                tmp_cursor.close()
                tmp_conn.close()

                conn = mysql.connector.connect(**DB_CONFIG)
                return conn
            except mysql.connector.Error as err2:
                print(f"Falha ao criar/abrir o banco: {err2}")
                return None
        elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Erro: usuário ou senha incorretos.")
        else:
            print(f"Erro ao conectar: {err}")
        return None



def init_db():
    con = get_connection()
    if con is None:
        print("Falha ao conectar ao DB.")
        return

    cursor = con.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                IdUsuario INT PRIMARY KEY AUTO_INCREMENT,
                Email VARCHAR(255) NOT NULL UNIQUE,
                Senha VARCHAR(255) NOT NULL,
                Nome VARCHAR(255) NOT NULL,
                DataCriacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                IdProduto INT PRIMARY KEY AUTO_INCREMENT,
                NomeProduto VARCHAR(255) NOT NULL,
                Preco DECIMAL(10, 2) NOT NULL,
                Quantidade INT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                IdCompra INT PRIMARY KEY AUTO_INCREMENT,
                IdUsuario INT,
                DataCompra DATETIME NOT NULL,
                Total DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (IdUsuario) REFERENCES usuarios(IdUsuario)
            )
        """)

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

        cursor.execute("SELECT COUNT(*) FROM produtos")
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute(
                "INSERT INTO produtos (NomeProduto, Preco, Quantidade) VALUES (%s, %s, %s)",
                ("Pão de Forma Integral", 8.50, 100)
            )

        con.commit()
        print("Banco inicializado com sucesso.")

    except mysql.connector.Error as err:
        print(f"Erro ao inicializar DB: {err}")
    finally:
        cursor.close()
        con.close()


init_db()



@app.route("/")
@requer_login
def index():
    return render_template("index.html")


@app.route('/login')
def login():
    if 'usuario_id' in session:
        return redirect(url_for('index'))
    return render_template('auth.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    if not all([nome, email, senha]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    if len(senha) < 6:
        return jsonify({'error': 'A senha deve ter pelo menos 6 caracteres'}), 400
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': 'Email inválido'}), 400

    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

    con = get_connection()
    if con is None:
        return jsonify({'error': 'Erro de conexão com o banco'}), 500

    cursor = con.cursor()
    try:
        cursor.execute('SELECT * FROM usuarios WHERE Email=%s', (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email já cadastrado'}), 400

        cursor.execute('INSERT INTO usuarios (Nome, Email, Senha) VALUES (%s, %s, %s)',
                       (nome, email, senha_hash))
        con.commit()
        return jsonify({'message': 'Usuário cadastrado com sucesso!'})
    except mysql.connector.Error as err:
        con.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        con.close()


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')

    if not all([email, senha]):
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    con = get_connection()
    if con is None:
        return jsonify({'error': 'Erro de conexão com o banco'}), 500

    cursor = con.cursor(dictionary=True)
    cursor.execute('SELECT * FROM usuarios WHERE Email=%s', (email,))
    usuario = cursor.fetchone()

    if not usuario:
        return jsonify({'error': 'Email ou senha incorretos'}), 401

    if not bcrypt.checkpw(senha.encode('utf-8'), usuario['Senha'].encode('utf-8')):
        return jsonify({'error': 'Email ou senha incorretos'}), 401

    session['usuario_id'] = usuario['IdUsuario']
    session['usuario_nome'] = usuario['Nome']
    session['usuario_email'] = usuario['Email']

    return jsonify({
        'message': 'Login realizado com sucesso!',
        'usuario': {
            'id': usuario['IdUsuario'],
            'nome': usuario['Nome'],
            'email': usuario['Email']
        }
    })



@app.route("/api/products", methods=["GET"])
def list_products():
    con = get_connection()
    if con is None:
        return jsonify({"error": "Erro de conexão com o DB."}), 500

    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()
    con.close()
    return jsonify(rows)


@app.route("/api/products", methods=["POST"])
@requer_admin
def add_product():
    data = request.json
    con = get_connection()
    if con is None:
        return jsonify({"error": "Erro de conexão com o DB."}), 500

    cursor = con.cursor()
    query = "INSERT INTO produtos (NomeProduto, Preco, Quantidade) VALUES (%s, %s, %s)"
    values = (data["NomeProduto"], data["Preco"], data["Quantidade"])

    try:
        cursor.execute(query, values)
        con.commit()
        return jsonify({"message": "Produto adicionado com sucesso!", "IdProduto": cursor.lastrowid})
    except mysql.connector.Error as err:
        con.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        con.close()


@app.route("/api/products/<int:id>", methods=["PUT"])
@requer_admin
def update_product(id):
    data = request.json
    con = get_connection()
    if con is None:
        return jsonify({"error": "Erro de conexão com o DB."}), 500

    cursor = con.cursor()
    query = "UPDATE produtos SET NomeProduto=%s, Preco=%s, Quantidade=%s WHERE IdProduto=%s"
    values = (data["NomeProduto"], data["Preco"], data["Quantidade"], id)

    try:
        cursor.execute(query, values)
        con.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Produto não encontrado."}), 404
        return jsonify({"message": "Produto atualizado com sucesso!"})
    except mysql.connector.Error as err:
        con.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        con.close()


@app.route("/api/products/<int:id>", methods=["DELETE"])
@requer_admin
def delete_product(id):
    con = get_connection()
    if con is None:
        return jsonify({"error": "Erro de conexão com o DB."}), 500

    cursor = con.cursor()
    try:
        cursor.execute("DELETE FROM produtos WHERE IdProduto=%s", (id,))
        con.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Produto não encontrado."}), 404
        return jsonify({"message": "Produto removido com sucesso!"})
    except mysql.connector.Error as err:
        con.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        con.close()


# --- Registrar compra ---
@app.route("/api/purchase", methods=["POST"])
def purchase():
    if 'usuario_id' not in session:
        return jsonify({"error": "Usuário não autenticado."}), 401

    data = request.json
    if 'cart' not in data or not isinstance(data['cart'], list):
        return jsonify({"error": "Carrinho inválido."}), 400

    usuario_id = session['usuario_id']
    con = get_connection()
    cursor = con.cursor()
    total = 0
    items = []

    try:
        con.start_transaction()
        for item in data["cart"]:
            cursor.execute("SELECT NomeProduto, Preco, Quantidade FROM produtos WHERE IdProduto=%s FOR UPDATE",
                           (item["IdProduto"],))
            produto = cursor.fetchone()
            if not produto:
                con.rollback()
                return jsonify({"error": "Produto não encontrado."}), 404
            nome, preco, estoque = produto
            if estoque < item["Quantidade"]:
                con.rollback()
                return jsonify({"error": f"Estoque insuficiente para {nome}."}), 400

            subtotal = float(preco) * item["Quantidade"]
            total += subtotal
            items.append({
                "IdProduto": item["IdProduto"],
                "NomeProduto": nome,
                "Preco": float(preco),
                "Quantidade": item["Quantidade"],
                "Subtotal": subtotal
            })

            cursor.execute("UPDATE produtos SET Quantidade=Quantidade-%s WHERE IdProduto=%s",
                           (item["Quantidade"], item["IdProduto"]))

        data_compra = datetime.now()
        cursor.execute("INSERT INTO compras (IdUsuario, DataCompra, Total) VALUES (%s, %s, %s)",
                       (usuario_id, data_compra, total))
        id_compra = cursor.lastrowid

        for item in items:
            cursor.execute("""
                INSERT INTO itens_compra (IdCompra, IdProduto, NomeProduto, Preco, Quantidade, Subtotal)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_compra, item["IdProduto"], item["NomeProduto"], item["Preco"], item["Quantidade"], item["Subtotal"]))

        con.commit()

    except mysql.connector.Error as err:
        con.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        con.close()

    return jsonify({
        "itens": items,
        "total": round(total, 2),
        "data": data_compra.strftime("%d/%m/%Y %H:%M:%S")
    })


# --- Histórico de compras ---
@app.route("/api/history", methods=["GET"])
def get_history():
    if 'usuario_id' not in session:
        return jsonify({"error": "Usuário não autenticado."}), 401

    usuario_id = session['usuario_id']
    usuario_email = session.get('usuario_email')

    con = get_connection()
    cursor = con.cursor(dictionary=True)

    if usuario_email == 'admin@gmail.com':
        cursor.execute("SELECT * FROM compras ORDER BY DataCompra DESC")
    else:
        cursor.execute("SELECT * FROM compras WHERE IdUsuario=%s ORDER BY DataCompra DESC", (usuario_id,))

    compras = cursor.fetchall()
    historico = []
    for compra in compras:
        cursor.execute("SELECT NomeProduto, Preco, Quantidade, Subtotal FROM itens_compra WHERE IdCompra=%s",
                       (compra["IdCompra"],))
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
