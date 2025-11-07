from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from src.config.data_base import init_db, db
from src.routes import init_routes
from src.Infrastructure.Model.user import User
import os  

def create_app():
    """
    Cria e configura a aplicação Flask.
    """
    app = Flask(__name__)
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
    jwt = JWTManager(app)  


    init_db(app)
    init_routes(app)

    with app.app_context():
        db.create_all()
        # Criar usuário admin se não existir
        from src.Application.Service.user_service import UserService
        UserService.create_admin_if_not_exists()
        print("Tabelas criadas e usuário admin verificado!")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)