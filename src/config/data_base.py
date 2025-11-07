from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text

db = SQLAlchemy()

DB_CONFIG = {
    'user': 'root',
    'password': '218101809Luiz.',
    'host': 'localhost',
    'database': 'projeto_frameworks'
}


def init_db(app):
    """
    Inicializa a base de dados com o app Flask e o SQLAlchemy usando MySQL.
    Cria o database se necessário conectando ao servidor (sem especificar database)
    e então configura a URI para o SQLAlchemy usar o database criado.
    """
    # Cria o database se não existir. Conecta ao servidor sem database.
    base_uri = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/"
    engine = create_engine(base_uri)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}"))

    # Configuração MySQL para a aplicação (com database)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa a conexão do Flask-SQLAlchemy
    db.init_app(app)
