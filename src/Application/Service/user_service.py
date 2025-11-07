from src.Domain.user import UserDomain
from src.Infrastructure.Model.user import User
from src.config.data_base import db
from src.Infrastructure.http.whats_app import WhatsAppService

import os 

# Prefer environment variables for Twilio credentials; keep previous values as fallback
account_sid = os.environ.get('TWILIO_ACCOUNT_SID', "[REMOVED_TWILIO_SID]")
auth_token = os.environ.get('TWILIO_AUTH_TOKEN', "d670018102f5d2fd131010b7f404f621")
from_whatsapp_number = os.environ.get('TWILIO_FROM_NUMBER', "whatsapp:+14155238886")


class UserService:
    @staticmethod
    def create_admin_if_not_exists():
        # Verifica se o admin já existe
        admin = User.query.filter_by(email='luiz@gmail.com').first()
        if not admin:
            # Cria o usuário admin com os dados especificados
            admin = User(
                name='luiz',
                email='luiz@gmail.com',
                password='1234luiz',
                cnpj='49433805810',  # CPF no lugar do CNPJ conforme especificado
                celular='11979911839',
                codigo_validacao=None,
                status=2  # Status 2 para administrador
            )
            db.session.add(admin)
            db.session.commit()
        else:
            # Se já existe, garante que o status é 2
            if admin.status != 2:
                admin.status = 2
                db.session.commit()
        return admin

    @staticmethod
    def create_user(name, email, password, cnpj=None, celular=None):
        # Usa valores padrão já que não coletamos mais
        cnpj = cnpj or '00000000000'
        celular = celular or '11979911839'
        
        # Não envia código aqui - será enviado na rota /send-code
        new_user = UserDomain(name, email, password, cnpj, celular, codigo_validacao=None, status=1)
        user = User(
            name=new_user.name,
            email=new_user.email,
            password=new_user.password,
            cnpj=new_user.cnpj,
            celular=new_user.celular,
            codigo_validacao=None,
            status=1  # Status 1 para usuários comuns
        )


       
        db.session.add(user)
        db.session.commit()
        return user
    

    @staticmethod
    def validar_codigo(codigo_digitado):
        """Valida o código diretamente contra o último código gerado"""
        from src.Infrastructure.http.whats_app import verificar_codigo
        return verificar_codigo(codigo_digitado)


       
    @staticmethod
    def verifica_user(email, password):
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return None, "Usuário não encontrado"
        
        if user.password != password:
            return None, "Senha incorreta"
        
        if not user.status:
            return None, "Usuário precisa validar o código"
        
        return user, "Usuário logado"
    
    @staticmethod
    def put_user(id, name = None, email = None, password = None, cnpj = None, celular = None):
        user = User.query.filter_by(id = id).first()

        if name:
            user.name = name
        if email:
            user.email = email
        if password is not None:
            user.password = password
        if cnpj:
            user.cnpj = cnpj
        if celular:
            user.celular = celular

        db.session.commit()
        return user.to_dict()
            
    @staticmethod
    def resgata_user(id):
        user = User.query.filter_by(id = id).first()
        if not user:
            return None
        else:
            return user.to_dict()

    @staticmethod
    def deletar_user(id):
        user = User.query.filter_by(id=id).first()
        if not user:
            return False
        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return None