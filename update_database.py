from flask import Flask
from src.config.data_base import init_db, db

def update_database():
    # Criar uma aplicação Flask temporária para o contexto do banco de dados
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/projeto_frameworks'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar o banco de dados
    init_db(app)
    
    with app.app_context():
        try:
            from sqlalchemy import text
            # Atualizar o tamanho do campo imagem na tabela produtos
            db.session.execute(text("ALTER TABLE produtos MODIFY COLUMN imagem VARCHAR(500)"))
            db.session.commit()
            print("Campo 'imagem' atualizado para VARCHAR(500) com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar banco de dados: {str(e)}")

if __name__ == '__main__':
    update_database()
