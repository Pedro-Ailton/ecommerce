from db import db
import datetime
from sqlalchemy import func
from enum import Enum
from zoneinfo import ZoneInfo

offset = datetime.timedelta(hours= -3)

class TipoMovimentacao(Enum):
    ENTRADA = 'entrada'
    SAIDA = 'saida'


class Produtos(db.Model):
    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(100), nullable = False)
    descricao = db.Column(db.Text, nullable = True)
    preco = db.Column(db.Numeric(3,2), nullable = False)

    imagens = db.relationship(
        'ImagemProduto',
        backref='produto',
        cascade='all, delete-orphan',
        lazy=True
    )

class ImagemProduto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(
        db.Integer,
        db.ForeignKey('produtos.id'),
        nullable=False
    )
    arquivo = db.Column(db.String(255), nullable=False)
    principal = db.Column(db.Boolean, default=False)
    

class Categorias(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(50), nullable = False)

class Estoque(db.Model):
    __tablename__ = "estoque"

    id =  db.Column(db.Integer, primary_key = True)
    tamanho = db.Column(db.String(3), nullable = False)
    cor = db.Column(db.String(50), nullable = False)
    quantidade = db.Column(db.Integer, default = 0, nullable = False)

    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)

class Clientes(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(255), nullable = False)
    email = db.Column(db.String(255), nullable = False, unique = True)
    cpf = db.Column(db.String(14), nullable = False, unique = True)
    senha = db.Column(db.String(255), nullable = False)
    telefone = db.Column (db.String(15), nullable = True)


class Enderecos(db.Model):
    __tablename__ = "enderecos"

    id = db.Column(db.Integer, primary_key = True)
    cep = db.Column(db.String(9), nullable = False)
    endereco = db.Column(db.String(50), nullable = False)
    complemento = db.Column(db.String(100), nullable = True)
    numero = db.Column(db.Integer, nullable = False)
    bairro = db.Column(db.String(50), nullable = False)
    cidade = db.Column(db.String(50), nullable = False)
    estado = db.Column(db.String(25), nullable = False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)


class Admins(db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(255), nullable = False)
    email = db.Column(db.String(255), nullable = False, unique = True)
    senha = db.Column(db.String(255), nullable = False)

class Categoria_Produto(db.Model):
    __tablename__ = "categoria_produto"
    id = db.Column(db.Integer, primary_key = True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable = False)

class Pedidos(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key = True)
    cliente_id = db.Column(db.Integer, nullable = False)
    produto_id = db.Column(db.Integer, nullable = False)
    valor = db.Column(db.Numeric(5,2), nullable = False)
    data_pedido = db.Column(db.DateTime, server_default=func.now(), nullable=False)

class Movimentacoes(db.Model):
    __tablename__ ="movimentacoes"

    id = db.Column(db.Integer, primary_key = True)
    tipo = db.Column(db.Enum(TipoMovimentacao), nullable = False)
    quantidade = db.Column(db.Integer, nullable= False)
    data_mov = db.Column(db.DateTime, default=lambda: datetime.now(datetime.timezone.utc), nullable=False)

    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable = False)
    estoque_id = db.Column(db.Integer, db.ForeignKey('estoque.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)

    produto = db.relationship('Produtos', backref='movimentacoes')
    estoque = db.relationship('Estoque', backref='movimentacoes')
    admin = db.relationship('Admins', backref='movimentacoes')

    @property
    def data_mov_br(self):
        if self.data_mov.tzinfo is None:
            dt = self.data_mov.replace(tzinfo=datetime.timezone.utc)
        else:
            dt = self.data_mov
        return dt.astimezone(ZoneInfo("America/Sao_Paulo"))