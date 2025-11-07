from flask import Flask
from src.config.data_base import init_db, db
from src.Infrastructure.Model.user import User

def create_admin_user():
    # Criar uma aplicação Flask temporária para o contexto do banco de dados
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/projeto_frameworks'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar o banco de dados
    init_db(app)
    
    with app.app_context():
        # Verificar se o admin já existe
        existing_admin = User.query.filter_by(email='luiz@gmail.com').first()
        if existing_admin:
            print("Usuário admin já existe. Atualizando para status 2...")
            existing_admin.status = 2
            db.session.commit()
            print("Status do admin atualizado com sucesso!")
        else:
            # Criar o novo usuário admin
            admin = User(
                name='luiz',
                email='luiz@gmail.com',
                password='1234luiz',
                cnpj='49433805810',  # CPF como solicitado
                celular='11979911839',
                codigo_validacao=None,
                status=2  # Status 2 para administrador
            )
            
            try:
                db.session.add(admin)
                db.session.commit()
                print("Usuário admin criado com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao criar usuário admin: {str(e)}")

if __name__ == '__main__':
    create_admin_user()
