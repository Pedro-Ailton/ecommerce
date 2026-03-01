import os
import shutil
from db import db
from models import Admins, Produtos, ImagemProduto

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_IMG_DIR = os.path.join(BASE_DIR, 'seed', 'imagens')
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads', 'produtos')

def init_datas():
        
    admin1 = Admins(
        nome = "Admin",
        email = "admin@email.com",
        senha = "senha123"
    )

    admin_cadastrado = Admins.query.filter_by(email = "admin@email.com").first()

    if not admin_cadastrado:
        db.session.add(admin1)
        db.session.commit()

    produto1 = Produtos(
        nome = "Tênis Esportivo",
        descricao = "Tênis confortável e ideal para esportes.",
        preco = 210.00
    )

    produto_cadastrado = Produtos.query.filter_by(nome = "Tênis Esportivo").first()

    if not produto_cadastrado:
        db.session.add(produto1)
        db.session.commit()
    
    origem = os.path.join(SEED_IMG_DIR, 'tenis.jpg')
    destino = os.path.join(UPLOAD_DIR, 'tenis.jpg')

    shutil.copy(origem, destino)

    imagem = ImagemProduto(
        produto_id=produto_cadastrado.id,
        arquivo='tenis.jpg',
        principal=True
    )

    imagem_cadastrada = ImagemProduto.query.filter_by(arquivo='tenis.jpg').first()
    if not imagem_cadastrada:
        db.session.add(imagem)
        db.session.commit()