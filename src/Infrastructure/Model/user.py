from src.config.data_base import db
from sqlalchemy import event

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(14), nullable=False)
    celular = db.Column(db.String(15), nullable=False)
    codigo_validacao = db.Column(db.String(10), nullable=True)
    status = db.Column(db.Integer, default=1, nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "cnpj": self.cnpj,
            "celular": self.celular,
            "codigo_validacao": self.codigo_validacao,
            "status": self.status
        }

# Evento para criar tabela com IF NOT EXISTS
@event.listens_for(User.__table__, 'after_create')
def create_users_table(*args, **kwargs):
    db.session.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        cnpj VARCHAR(14) NOT NULL,
        celular VARCHAR(15) NOT NULL,
        codigo_validacao VARCHAR(10),
        status INTEGER DEFAULT 1
    )
    """)

    


    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "cnpj": self.cnpj,
            "celular": self.celular,
            "codigo_validacao": self.codigo_validacao,
            "status": self.status
        }
