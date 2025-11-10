from src.Domain.user import UserDomain
from src.Infrastructure.Model.user import User
from src.config.data_base import db
from src.Infrastructure.http.whats_app import WhatsAppService
from werkzeug.security import generate_password_hash, check_password_hash

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
                password=generate_password_hash('1234luiz'),
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
            # Se senha do admin não está hasheada, migra para hash
            if admin.password and not str(admin.password).startswith('pbkdf2:'):
                try:
                    admin.password = generate_password_hash(admin.password)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
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
            password=generate_password_hash(new_user.password),
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
        if not email:
            return None, "Email não informado"
        if password is None:
            return None, "Senha não informada"

        email_norm = email.strip().lower()
        user = User.query.filter_by(email=email_norm).first() or User.query.filter_by(email=email.strip()).first()
        
        if not user:
            print(f"[LOGIN] Usuário não encontrado para email: {email_norm}")
            return None, "Usuário não encontrado"

        stored = user.password or ''
        provided = str(password)

        # Verifica se senha está hasheada
        is_hashed = str(stored).startswith('pbkdf2:')
        valid = False
        try:
            if is_hashed:
                valid = check_password_hash(stored, provided)
            else:
                valid = (stored == provided)
        except Exception:
            valid = False

        if not valid:
            print(f"[LOGIN] Senha incorreta para email: {email_norm} | hashed={is_hashed}")
            return None, "Senha incorreta"

        # Migração silenciosa: se estava em texto puro, converte para hash após login bem-sucedido
        if not is_hashed:
            try:
                user.password = generate_password_hash(provided)
                # também normaliza email para minúsculo
                user.email = email_norm
                db.session.commit()
                print(f"[LOGIN] Senha migrada para hash para email: {email_norm}")
            except Exception:
                db.session.rollback()
        
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