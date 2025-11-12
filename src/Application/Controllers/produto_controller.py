from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from src.Infrastructure.Model.produto import Produto
from src.Application.Service.produto_service import ProdutoService
import os
from werkzeug.utils import secure_filename
import uuid


class ProdutoController:
    @staticmethod
    def register_produto():
        # Verificar se é JSON ou form-data
        if request.is_json:
            # Dados vindos do frontend em JSON
            data = request.get_json()
            nome = data.get("name")
            preco = data.get("price")
            quantidade = data.get("quantity", 1)  # Default 1 se não fornecido
            status = data.get("status", True)
            imagem = data.get("image")  # URL da imagem
            
            if not all([nome, preco]):
                return jsonify({"erro": "Campos obrigatórios faltando (name, price)."}), 400
            
            try:
                # Criar produto com URL da imagem diretamente
                produto = ProdutoService.criar_produto(nome, float(preco), int(quantidade), status, imagem)
                
                return jsonify({
                    "id": produto.id,
                    "name": produto.nome,
                    "price": produto.preco,
                    "quantity": produto.quantidade,
                    "status": produto.status,
                    "image": produto.imagem,
                    "description": nome  # Usando nome como descrição
                }), 201
            except Exception as e:
                print(f"Erro ao criar produto: {str(e)}")  # Log do erro
                return jsonify({"erro": f"Erro ao criar produto: {str(e)}"}), 500
        else:
            # Dados vindos de form-data (mantém compatibilidade)
            nome = request.form.get("nome")
            preco = request.form.get("preco")
            quantidade = request.form.get("quantidade")
            status = request.form.get("status")
            imagem = request.files.get("imagem")
            
            if not all([nome, preco, quantidade]):
                return jsonify({"erro": "Campos obrigatórios faltando."}), 400

            
            upload_folder = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)

            imagem_path = None
            if imagem:
                filename = secure_filename(imagem.filename)
                unique = uuid.uuid4().hex
                safe_name = f"{unique}_{filename}" if filename else unique
                save_path = os.path.join(upload_folder, safe_name)
                imagem.save(save_path)
                imagem_path = f"/static/uploads/{safe_name}"

            produto = ProdutoService.criar_produto(nome, preco, quantidade, status, imagem_path)

            return jsonify({
                "id": produto.id,
                "nome": produto.nome,
                "preco": produto.preco,
                "quantidade": produto.quantidade,
                "status": produto.status,
                "imagem": produto.imagem
            }), 201
    

    @staticmethod
    def list_product():
        produtos = ProdutoService.listar_produtos()

        if produtos:
            # Retornar com os campos esperados pelo frontend
            return jsonify([{
                "id": p.id,
                "name": p.nome,
                "price": p.preco,
                "quantity": p.quantidade,
                "status": p.status,
                "image": p.imagem,
                "description": p.nome  # Usando nome como descrição por enquanto
            } for p in produtos])
        
        return jsonify([])
    
    @staticmethod
    def get_produto(id):
        from src.Infrastructure.Model.produto import Produto
        produto = Produto.query.filter_by(id=id).first()
        
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404
        
        return jsonify({
            "id": produto.id,
            "name": produto.nome,
            "price": produto.preco,
            "quantity": produto.quantidade,
            "status": produto.status,
            "image": produto.imagem,
            "description": produto.nome
        }), 200
    

    @staticmethod
    def att_produto(id):
        # Suporta JSON e multipart/form-data para atualização (inclui upload de imagem)
        if request.is_json:
            data = request.get_json()
            nome = data.get("name") or data.get("nome")
            preco = data.get("price") or data.get("preco")
            quantidade = data.get("quantity") or data.get("quantidade")
            imagem = data.get("image") or data.get("imagem")
        else:
            # multipart/form-data
            nome = request.form.get("name") or request.form.get("nome")
            preco = request.form.get("price") or request.form.get("preco")
            quantidade = request.form.get("quantity") or request.form.get("quantidade")
            imagem = request.files.get("imagem") or request.files.get("image")

        produto = ProdutoService.atualizar_produtos(
            id, nome=nome, preco=preco, quantidade=quantidade, imagem=imagem
        )

        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404
        
        return jsonify({
            "id": produto.id,
            "name": produto.nome,
            "price": produto.preco,
            "quantity": produto.quantidade,
            "status": produto.status,
            "image": produto.imagem,
            "description": produto.nome
        }), 200


    @staticmethod
    def vender(id):
        quantidade_venda = int(request.json.get("quantidade_venda", 1))

        produto, erro = ProdutoService.vender_produto(id, quantidade_venda)

        if erro:
            return jsonify({"erro": erro}), 400

        return jsonify({
            "message": "Venda realizada com sucesso!",
            "produto": produto.to_dict_product()
        }), 200
    

    @staticmethod
    def inativar_produto(id):
        """Inativar produto"""
        produto = ProdutoService.inativar_produto(id)
        
        if produto:
            return jsonify({
                "message": "Produto inativado com sucesso!",
                "produto": produto.to_dict_product()
            }), 200
        
        return jsonify({"erro": "Produto não encontrado"}), 404
    


    @staticmethod
    def ativar_produto(id):
        """Ativar produto"""
        produto = ProdutoService.ativar_produto(id)
        
        if produto:
            return jsonify({
                "message": "Produto ativado com sucesso!",
                "produto": produto.to_dict_product()
            }), 200
        
        return jsonify({"erro": "Produto não encontrado"}), 404
    

    @staticmethod
    def deletar_produto(id):

        produto = ProdutoService.excluir_produto(id)

        if produto:
            return jsonify({"message": "Produto excluído com sucesso"}), 200
        
        return jsonify({"message": "Erro ao excluir produto"}), 404




