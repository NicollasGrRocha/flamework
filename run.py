from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_cors import CORS
from src.config.data_base import init_db, db
from src.routes import init_routes
from src.Infrastructure.Model.user import User
import os  

def create_app():
    """
    Cria e configura a aplicação Flask.
    """
    app = Flask(__name__, static_folder="frontend/static", static_url_path="/static")
    app.secret_key = 'sua_chave_secreta_aqui'  # Adicione uma chave secreta para as sessões

    CORS(app)

    # CORS(app, resources={
    #     r"/*": {
    #         "origins": ["http://10.0.0.41:5000/"],
    #         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    #         "allow_headers": ["Content-Type", "Authorization"]
    #     }
    # })
    
  
    app.config["JWT_SECRET_KEY"] = "flaroque"  
    # Expiração de 24 horas para o token de acesso
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    jwt = JWTManager(app)  


    init_routes(app)

    # Inicialização do banco: permitir pular durante builds (ex.: Vercel) ou
    # falhas de conexão sem quebrar a importação do módulo.
    # Para pular, defina SKIP_DB_INIT=1 nas variáveis de ambiente do build.
    if os.environ.get("SKIP_DB_INIT") == "1":
        print("SKIP_DB_INIT=1 definido — pulando init_db e create_all")
    else:
        try:
            init_db(app)

            with app.app_context():
                # Importe TODOS os modelos antes do create_all para que as tabelas sejam criadas
                try:
                    from src.Infrastructure.Model.user import User  # noqa: F401
                    from src.Infrastructure.Model.produto import Produto  # noqa: F401
                    from src.Infrastructure.Model.order import Order  # noqa: F401
                    from src.Infrastructure.Model.order_item import OrderItem  # noqa: F401
                except Exception as e:
                    print(f"Erro ao importar modelos: {e}")

                db.create_all()

                # Criar usuário admin se não existir
                from src.Application.Service.user_service import UserService
                try:
                    UserService.create_admin_if_not_exists()
                except Exception as e:
                    print(f"Aviso: não foi possível criar/validar usuário admin: {e}")
                print("Tabelas criadas e usuário admin verificado!")
        except Exception as e:
            # Não parar a importação em caso de erro de DB durante build; imprimir aviso.
            print(f"Aviso: falha ao inicializar o banco de dados durante import: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)