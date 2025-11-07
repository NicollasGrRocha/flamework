from flask import request, jsonify, make_response
from flask_jwt_extended import create_access_token
from src.Application.Service.user_service import UserService


class UserController:
    @staticmethod
    def register_user():
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        cnpj = data.get('cnpj')
        celular = data.get('celular')

        if not name or not email or not password or not cnpj or not celular:
            return make_response(jsonify({"erro": "Missing required fields"}), 400)

        user = UserService.create_user(name, email, password, cnpj, celular)
        return make_response(jsonify({
            "mensagem": "User salvo com sucesso",
            "usuarios": user.to_dict()
        }), 200)
    
    @staticmethod
    def get_user(id):
        user = UserService.resgata_user(id)
        if not user:
            return jsonify({"message": "Usuário não encontrado"}), 404
        return jsonify({"Usuário encontrado": user}), 200
    

    @staticmethod
    def delete_user(id):
        result = UserService.deletar_user(id)
        if result is True:
            return jsonify({"message":"Usuário deletado com sucesso"}), 200
        elif result is False:
            return jsonify({"message": "Usuário não encontrado"}), 404
        else:
            return jsonify({"message": "Erro ao deletar o usuário"}), 500
    
    @staticmethod
    def validate_code():
        data = request.get_json()
        cnpj = data.get('cnpj')
        codigo_digitado = data.get('codigo_digitado')

        user,msg = UserService.validar_codigo(cnpj, codigo_digitado)

        if user:
            access_token = create_access_token(identity=str(user.cnpj))
            return jsonify({
                "message": msg,
                "token": access_token,
                "status": user.status
            }), 200
        else:
            return jsonify({"message": msg}), 401
        
        
    

    @staticmethod
    def verify_user():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user, msg = UserService.verifica_user(email, password)

        if user:
            # Gera um token JWT e retorna para o cliente
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                "message": "Usuário Logado", 
                "token": access_token,
                "status": user.status
            }), 200
        else:
            return jsonify({"message": msg}), 401
    
    @staticmethod
    def atualiza_user(id):
        data = request.get_json()
        user = UserService.put_user(
            id,
            name=data.get('name'),
            email=data.get('email'),
            password=data.get('password'),
            cnpj=data.get('cnpj'),
            celular=data.get('celular')
        )

        if not user:
            return jsonify({"message": "Usuário não encontrado"}), 404
        
        return jsonify({"message": "Usuário Atualizado", "user": user}), 200