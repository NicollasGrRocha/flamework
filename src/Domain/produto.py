class ProdutoDomain:
    def __init__(self, nome, preco, quantidade, status, imagem):
        self.nome = nome
        self.preco = preco
        self.quantidade = quantidade
        self.status = status
        self.imagem = imagem


    def to_dict_product(self):
        return {
            "nome": self.nome,
            "preco": self.preco,
            "quantidade": self.quantidade,
            "status": self.status,
            "imagem": self.imagem
        }