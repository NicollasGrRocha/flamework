from src.Domain.produto import ProdutoDomain
from src.Infrastructure.Model.produto import Produto
from werkzeug.utils import secure_filename
from src.config.data_base import db
from flask import current_app
import os 


class ProdutoService:
    @staticmethod
    def criar_produto(nome, preco, quantidade, status, imagem):
        # normaliza o campo status para boolean
        def _to_bool(val):
            if isinstance(val, bool):
                return val
            if val is None:
                return True
            s = str(val).strip().lower()
            if s in ('1', 'true', 't', 'yes', 'y', 'on', 'ativo', 'active'):
                return True
            if s in ('0', 'false', 'f', 'no', 'n', 'off', 'inativo', 'inactive'):
                return False
            # fallback: try integer
            try:
                return bool(int(s))
            except Exception:
                return True

        status_bool = _to_bool(status)
        
        # Converter preco e quantidade para os tipos corretos
        try:
            preco = float(preco)
            quantidade = int(quantidade)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Erro ao converter preco ou quantidade: {str(e)}")

        new_produto = ProdutoDomain(nome, preco, quantidade, status_bool, imagem)

        produto = Produto(
            nome = new_produto.nome,
            preco = new_produto.preco,
            quantidade = new_produto.quantidade,
            status = new_produto.status,
            imagem = new_produto.imagem
        )

        try:
            db.session.add(produto)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao salvar produto no banco: {str(e)}")
            
        return produto 
    

    @staticmethod
    def listar_produtos():
        return db.session.query(Produto).all()
    

    @staticmethod
    def atualizar_produtos(id, nome=None, preco=None, quantidade=None, imagem=None):
        new_produto = Produto.query.filter_by(id=id).first()
        
        if not new_produto:
            return None  
        
       
        if nome:
            new_produto.nome = nome
        
        if preco:
            new_produto.preco = preco
        
        if quantidade:
            new_produto.quantidade = quantidade
        
        if imagem:
            if hasattr(imagem, 'filename') and imagem.filename:  # É um FileStorage e tem nome?
                filename = secure_filename(imagem.filename)
                # Evita colisões usando UUID no nome do arquivo
                import uuid
                base, ext = os.path.splitext(filename)
                filename = f"{uuid.uuid4().hex}{ext or ''}"
                # Garante pasta absoluta
                upload_dir = os.path.join(current_app.static_folder, 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                abs_path = os.path.join(upload_dir, filename)
                imagem.save(abs_path)
                # salva caminho relativo iniciando com / para funcionar em páginas sob /static
                new_produto.imagem = f"/static/uploads/{filename}"
            else:
                # string/URL direta
                new_produto.imagem = imagem
        
        db.session.commit()
        return new_produto
    

    @staticmethod
    def inativar_produto(id):
        produto = Produto.query.filter_by(id=id).first()
    
        if not produto:
            return None
    
        produto.status = False  
        db.session.commit()
    
        return produto
    

    @staticmethod
    def ativar_produto(id):
        produto = Produto.query.filter_by(id=id).first()
        
        if not produto:
            return None
        
        produto.status = True  
        db.session.commit()
        
        return produto
    

    @staticmethod
    def excluir_produto(id):
        produto = Produto.query.filter_by(id = id).first()

        if not produto:
            return None
        
        db.session.delete(produto)
        db.session.commit()

        return True

    @staticmethod
    def vender_produto(id, quantidade_venda):
        produto = Produto.query.filter_by(id=id).first()
        
        if not produto:
            return None, "Produto não encontrado"

        if not produto.status:
            return None, "Produto inativo!"

        if produto.quantidade < quantidade_venda:
            return None, "Estoque insuficiente!"

        produto.quantidade -= quantidade_venda
        db.session.commit()

        return produto, None
    


    





