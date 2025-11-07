from src.Application.Controllers.user_controller import UserController
from src.Application.Controllers.produto_controller import ProdutoController
from flask import jsonify, make_response, request, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.Infrastructure.http.whats_app import gerar_codigo, verificar_codigo, ultimo_codigo

def init_routes(app):    
    @app.route("/api", methods=["GET"])
    def health():
        return make_response(jsonify({
            "mensagem": "API - OK; Docker - Up",
        }), 200)
    
    @app.route("/send-code", methods=["POST"])
    def send_code():
        try:
            from src.Infrastructure.Model.user import User
            from src.config.data_base import db
            
            data = request.get_json()
            if not data or not data.get("email"):
                return jsonify({"error": "Email é obrigatório"}), 400

            # Gerar e enviar o código primeiro
            codigo = gerar_codigo()

            if not codigo:
                return jsonify({"error": "Falha ao enviar código"}), 500

            print(f"Código gerado e enviado: {codigo}")  # Debug

            # Verificar se o usuário já existe para atualizar, senão cria um novo
            user = db.session.query(User).filter_by(email=data["email"]).first()

            if user:
                # Atualiza o código de validação do usuário existente
                user.codigo_validacao = codigo
                print(f"Atualizando código para usuário existente: {codigo}")  # Debug
            else:
                # Se não existe, cria um novo usuário com os dados básicos
                user = User(
                    name=data.get("name", ""),
                    email=data["email"],
                    password=data.get("password", ""),
                    cnpj="00000000000",
                    celular="11979911839",
                    codigo_validacao=codigo,
                    status=False
                )
                print(f"Criando novo usuário com código: {codigo}")  # Debug
                db.session.add(user)

            db.session.commit()
            return jsonify({"message": "Código enviado com sucesso"}), 200
            
        except Exception as e:
            print(f"Erro ao enviar código: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/verify-code", methods=["POST"])
    def verify_code():
        data = request.get_json()
        if not data or "code" not in data or "email" not in data:
            return jsonify({"error": "Código e email são obrigatórios"}), 400
            
        try:
            from src.Infrastructure.Model.user import User
            from src.config.data_base import db
            
            # Buscar usuário e verificar código
            user = db.session.query(User).filter_by(email=data["email"]).first()
            if not user:
                return jsonify({"error": "Usuário não encontrado"}), 404
                
            if not user.codigo_validacao:
                return jsonify({"error": "Nenhum código pendente. Solicite um novo código."}), 400
                
            if data["code"] != user.codigo_validacao:
                return jsonify({"error": "Código incorreto"}), 400
            
            # Atualizar dados do usuário se fornecidos
            if data.get("name"):
                user.name = data["name"]
            if data.get("password"):
                user.password = data["password"]
                
            # Se o código estiver correto, atualiza o status e limpa o código
            user.status = True
            user.codigo_validacao = None
            db.session.commit()
            
            return jsonify({"message": "Código validado com sucesso. Você já pode fazer login."}), 200
            
        except Exception as e:
            print(f"Erro na verificação do código: {str(e)}")
            return jsonify({"error": "Erro ao verificar código"}), 500
        if not data.get("name") or not data.get("email") or not data.get("password"):
                return jsonify({"error": "Dados de cadastro incompletos"}), 400
            
        try:
                # Primeiro verifica se o email já existe
                from src.Infrastructure.Model.user import User
                from src.config.data_base import db
                existing_user = db.session.query(User).filter_by(email=data["email"]).first()
                if existing_user:
                    return jsonify({"error": "Este email já está cadastrado. Por favor, use outro email ou faça login."}), 400
                
                # Se o email não existe, prepara os dados para o registro
                request._cached_json = (dict(
                    name=data["name"],
                    email=data["email"],
                    password=data["password"],
                    cnpj="00000000000",  # valor padrão
                    celular="11979911839"  # número fixo
                ), True)
                
                # Usar o UserController que já tem a lógica de criar usuário
                return UserController.register_user()
                
        except Exception as e:
                print(f"Erro ao criar usuário: {str(e)}")  # log para debug
                if "Duplicate entry" in str(e):
                    return jsonify({"error": "Este email já está cadastrado. Por favor, use outro email ou faça login."}), 400
                return jsonify({"error": "Erro ao criar usuário. Por favor, tente novamente."}), 500
                
        return jsonify({"error": message}), 400
    
    @app.route("/user", methods=["POST"])
    def register_user():
        return UserController.register_user()
    
    @app.route("/user/<int:id>", methods=["GET"])
    @jwt_required()
    def get_user(id):
        return UserController.get_user(id)
    
    @app.route("/verifica", methods=["POST"])
    def verify():
        try:
            data = request.get_json()
            if not data or "email" not in data or "password" not in data:
                return jsonify({"error": "Email e senha são obrigatórios"}), 400

            # Buscar usuário pelo email
            from src.Infrastructure.Model.user import User
            from src.config.data_base import db
            user = db.session.query(User).filter_by(email=data["email"]).first()
            
            if not user:
                return jsonify({"error": "Usuário não encontrado"}), 404
            
            # Verifica a senha (usa o UserController que retorna (response, status) ou Response)
            result = UserController.verify_user()

            # Interpretar o resultado para obter o status code de forma segura
            status_code = None
            try:
                if isinstance(result, tuple):
                    # result normalmente é (response, status_code)
                    _, status = result
                    if isinstance(status, int):
                        status_code = status
                    else:
                        # Caso incomum: status pode ser um objeto Response
                        status_code = getattr(status, 'status_code', None)
                else:
                    # result pode ser um Response
                    status_code = getattr(result, 'status_code', None)
            except Exception:
                status_code = None

            # Se a verificação for bem sucedida (HTTP 200), atualiza o status
            if status_code == 200:
                user.status = True  # Atualiza o status para verificado
                db.session.commit()

            return result

        except Exception as e:
            print(f"Erro na verificação: {str(e)}")
            return jsonify({"error": "Erro ao verificar usuário"}), 500
    
    @app.route("/user/<int:id>", methods=["PUT"])
    @jwt_required()
    def update_user(id):
        return UserController.atualiza_user(id)
    
    @app.route("/verifica/code", methods=["POST"])
    def validation_code():
        return UserController.validate_code()

    @app.route("/user/<int:id>", methods=["DELETE"])
    @jwt_required()
    def delete_user(id):
        return UserController.delete_user(id)
    
    @app.route("/produto", methods=["POST"])
    def criar_produto():
        return ProdutoController.register_produto()
    
    @app.route("/produto", methods=["GET"])
    def listar():
        return ProdutoController.list_product()
    
    @app.route("/produto/<int:id>", methods=["GET"])
    def get_produto(id):
        return ProdutoController.get_produto(id)
    
    @app.route("/produto/<int:id>", methods=["PUT"])
    def att_produto(id):
        return ProdutoController.att_produto(id)
    
    @app.route("/ativar/<int:id>", methods=["PATCH"])
    def ativar_product(id):
        return ProdutoController.ativar_produto(id)
    
    @app.route("/desativar/<int:id>", methods=["PATCH"])
    def desativar_product(id):
        return ProdutoController.inativar_produto(id)
    
    @app.route("/produto/<int:id>", methods=["DELETE"])
    def exclusao_produto(id):
        return ProdutoController.deletar_produto(id)
    
    @app.route("/produto/vender/<int:id>", methods=["PATCH"])
    def vender_produto(id):
        return ProdutoController.vender(id)

    return app
