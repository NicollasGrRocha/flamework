from src.config.data_base import db
from sqlalchemy import event

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(100), nullable = False)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable = False)
    status = db.Column(db.Boolean, default=True, nullable=True)
    imagem = db.Column(db.String(500))  # Aumentado para 500 para suportar URLs longas
    def to_dict_product(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "preco": self.preco,
            "quantidade": self.quantidade,
            "status": self.status,
            "imagem": self.imagem
        }


# Evento para criar tabela com IF NOT EXISTS
@event.listens_for(Produto.__table__, 'after_create')
def create_produtos_table(*args, **kwargs):
    db.session.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        nome VARCHAR(100) NOT NULL,
        preco FLOAT NOT NULL,
        quantidade INTEGER NOT NULL,
        status BOOLEAN DEFAULT TRUE,
        imagem VARCHAR(500)
    )
    """)