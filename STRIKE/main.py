from flask import Flask, render_template, request, redirect, session, url_for, flash, current_app
from sqlalchemy import func
from db import db
from models import Produtos,ImagemProduto, Categoria_Produto, Categorias, Estoque, Clientes, Enderecos, Admins, Movimentacoes
from seed import init_datas
import os
from dotenv import load_dotenv, dotenv_values 
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# =================== Conexão com o banco de dados ===================

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
db.init_app(app)

# =================== Página inicial ===================

@app.route('/')
def index():
    banners = ['Img/BANNERS/BANNER-1.png']
    if 'usuario' in session and session.get('tipo') == 'Cliente':
        cliente = Clientes.query.filter_by(email=session['usuario']).first()
        
        nome_usuario = cliente.nome if cliente else 'Usuário Desconhecido'
        produtos = db.session.execute(db.select(Produtos)).scalars().all()
        imagens = db.session.execute(db.select(ImagemProduto)).scalars().all()
        return render_template('index.html', usuario=session['usuario'], produtos=produtos, nome_usuario=nome_usuario, imagens=imagens, banners = banners)
    else:
        produtos = db.session.execute(db.select(Produtos)).scalars().all()
        imagens = db.session.execute(db.select(ImagemProduto)).scalars().all()
        return render_template('index.html',produtos=produtos,banners = banners, imagens=imagens)



    

# =================== Login ===================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        tipo = request.form['usuario']
        email = request.form['email']
        senha = request.form['senha']

        usuario = None

        if tipo == 'Administrador':
            usuario = Admins.query.filter_by(email=email, senha=senha).first()
        elif tipo == 'Cliente':
            usuario = Clientes.query.filter_by(email=email, senha=senha).first()
        else:
            flash("Tipo de usuário inválido.")
            return render_template('login.html')
        
        if usuario:
            session['usuario'] = usuario.email
            session['tipo'] = tipo

            if tipo == 'Administrador':
                return redirect('/admin')
            elif tipo == 'Cliente':
                return redirect('/')
        else:
            flash('Usuário ou senha incorretos')

    return render_template('login.html')


# =================== Finalizar compra ===================

@app.route('/finalizar-compra')
def finalizar_compra():
    if 'usuario' not in session:
        flash('Você precisa estar logado para finalizar a compra.')
        return redirect(url_for('login'))

    return render_template('add_end.html')


# =================== Painel do administrador ===================

@app.route('/admin')
def admin():
    if 'usuario' in session and session.get('tipo') == 'Administrador':
        produtos = Produtos.query.all()
        imagens = db.session.execute(db.select(ImagemProduto)).scalars().all()
        # Buscar administrador pelo email
        administrador = Admins.query.filter_by(email=session['usuario']).first()
        
        banners = ['Img/BANNERS/BANNER-1.png']
        nome_usuario = administrador.nome if administrador else 'Usuário Desconhecido'
        
        return render_template('admin.html', 
                             usuario=session['usuario'], 
                             produtos=produtos, 
                             banners=banners, 
                             nome_usuario=nome_usuario,
                            imagens=imagens)
    else:
        return redirect('/')


# =================== Rota para adicionar produtos (via formulário) ===================

@app.route('/admin/adicionar', methods=['GET', 'POST'])
def adicionar_item():
    if 'usuario' in session and session.get('tipo') == 'Administrador':
        if request.method == 'POST':
            nome = request.form.get('nome_produto')
            descricao = request.form.get('descricao')
            preco = request.form.get('preco')

            if not nome or not preco:
                flash("Campos obrigatórios não foram preenchidos!")
                return redirect(request.url)

            # Criar novo produto
            novo_produto = Produtos(
                nome=nome,
                descricao=descricao,
                preco=float(preco)
            )
            
            db.session.add(novo_produto)
            db.session.commit()

            return redirect(url_for('admin'))

        return render_template('adicionar.html')
    else:
        return redirect('/')


# =================== Rota para deletar produtos (via formulário) ===================

@app.route('/admin/deletar', methods=['POST'])
def deletar_item():
    if 'usuario' in session and session.get('tipo') == 'Administrador':
        id = int(request.form['id'])

        produto = Produtos.query.get(id)
        if produto:
            db.session.delete(produto)
            db.session.commit()
            flash("Produto deletado com sucesso!")
        else:
            flash("Produto não encontrado!")

        return redirect('/admin')
    else:
        return redirect('/')


# ================= Rota para exibir o formulário para deletar os produtos ================

@app.route('/admin/deletar', methods=['GET'])
def pagina_deletar():
    if 'usuario' in session and session.get('tipo') == 'Administrador':
        return render_template('deletar.html')
    else:
        return redirect('/')

# ================= Rota para gerenciar o estoque ===================
@app.route('/admin/estoque', methods=['GET', 'POST'])
def gerenciar_estoque():
    if 'usuario' in session and session.get('tipo') == 'Administrador':
        produtos = Produtos.query.all()
        estoque = Estoque.query.all()
        movimentacoes = Movimentacoes.query.all()

        if request.method == 'POST':
            produto_id = request.form.get('produto_id')
            quantidade = request.form.get('quantidade')
            tamanho = request.form.get('tamanho')
            cor = request.form.get('cor')
            tipo_movimentacao = request.form.get('tipo_movimentacao')
            

            if not all([produto_id, quantidade, tamanho, cor, tipo_movimentacao]):
                flash("Todos os campos devem ser preenchidos!")
                return redirect('/admin/estoque')
            
            quantidade = int(quantidade)

            estoque_item = Estoque.query.filter_by(produto_id = produto_id, tamanho = tamanho, cor = cor).first()

            if not estoque_item:
                if tipo_movimentacao == "SAIDA":
                    flash('Não é possível dar saída em um item sem estoque.')
                    return redirect('/admin/estoque')
                
                estoque_item = Estoque(
                    produto_id = produto_id,
                    tamanho = tamanho,
                    cor = cor,
                    quantidade = 0
                )
                db.session.add(estoque_item)
                
                if tipo_movimentacao == "ENTRADA":
                    estoque_item.quantidade += quantidade

                elif tipo_movimentacao == "SAIDA":
                    if estoque_item.quantidade < quantidade:
                        flash('Quantidade insuficiente no estoque!')
                        return redirect('admin/estoque')
                    else:
                        estoque_item.quantidade -= quantidade
                        return redirect('admin/estoque')

                else:
                    flash=('Tipo de registro inválido')
                    return redirect('admin/estoque')
            else:
                if tipo_movimentacao == "ENTRADA":
                    estoque_item.quantidade += quantidade
                    admin = Admins.query.filter_by(email=session['usuario']).first()
                
                    nova_movimentacao = Movimentacoes(
                                produto_id=produto_id,
                                data_mov= func.now(),
                                tipo=tipo_movimentacao,
                                quantidade = int(quantidade),
                                estoque_id = estoque_item.id,
                                admin_id = admin.id
                            )
                    db.session.add(nova_movimentacao)
                    db.session.commit()
                    return redirect('estoque')

                elif tipo_movimentacao == "SAIDA":
                    if estoque_item.quantidade < quantidade:
                        flash('Quantidade insuficiente no estoque!')
                        return redirect('admin/estoque')
                    else:
                        estoque_item.quantidade -= quantidade
                        admin = Admins.query.filter_by(email=session['usuario']).first()
                
                        nova_movimentacao = Movimentacoes(
                                produto_id=produto_id,
                                data_mov= func.now(),
                                tipo=tipo_movimentacao,
                                quantidade = int(quantidade),
                                estoque_id = estoque_item.id,
                                admin_id = admin.id
                            )
                        db.session.add(nova_movimentacao)
                        db.session.commit()
                        return redirect('estoque')
                else:
                    flash=('Tipo de registro inválido')
                    return redirect('admin/estoque')
            
                

                
            admin = Admins.query.filter_by(email=session['usuario']).first()
                
            nova_movimentacao = Movimentacoes(
                    produto_id=produto_id,
                    data_mov= func.now(),
                    tipo=tipo_movimentacao,
                    quantidade = int(quantidade),
                    estoque_id = estoque_item.id,
                    admin_id = admin.id
                )
            db.session.add(nova_movimentacao)
            db.session.commit()
            
            return redirect('/admin/estoque')
        return render_template('gerenciar_estoque.html', produtos = produtos, estoque = estoque, movimentacoes = movimentacoes)
    else:
        return redirect('/')

# =================== Logout ===================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# =================== Nova senha ===================

@app.route('/nova-senha', methods=['GET', 'POST'])
def up_senha():
    if request.method == 'POST':
        email_form = request.form['email']
        senha1 = request.form['senha1']
        senha2 = request.form['senha2']

        if not email_form or not senha1 or not senha2:
            flash("Todos os campos devem ser preenchidos!")
            return render_template('up-senha.html')

        if senha1 != senha2:
            flash("Senhas não coincidem")
            return render_template('up-senha.html')

        cliente = Clientes.query.filter_by(email=email_form).first()

        if cliente:
            cliente.senha = senha1
            db.session.commit()
            flash("Senha alterada com sucesso!")
            return redirect(url_for('login'))
        else:
            flash("Email não encontrado.")

    return render_template('up-senha.html')


# =================== Cadastro de clientes  ===================

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha1 = request.form['senha1']
        senha2 = request.form['senha2']
        cpf = request.form['cpf']
        telefone = request.form['telefone']

        if not nome or not email or not senha1 or not senha2 or not cpf or not telefone:
            flash("Todos os campos devem ser preenchidos!")
            return render_template('cadastro.html')

        if senha1 != senha2:
            flash("Senhas não coincidem!")
            return render_template('cadastro.html')

        email_existente = Clientes.query.filter_by(email=email).first()
        cpf_existente = Clientes.query.filter_by(cpf=cpf).first()

        if email_existente:
            flash("Email já cadastrado!")
            return render_template('cadastro.html')
        if cpf_existente:
            flash("CPF já cadastrado!")
            return render_template('cadastro.html')
        novo_cliente = Clientes(
            nome=nome,
            email=email,
            senha=senha1,
            cpf = cpf,
            telefone = telefone
        )
        
        db.session.add(novo_cliente)
        db.session.commit()

        flash("Cadastro realizado com sucesso!")
        return redirect('/login')

    return render_template('cadastro.html')

# =================== Página do Produto ====================

@app.route('/produto/<int:id>', methods=['GET', 'POST'])
def produto(id):
    produto = Produtos.query.get(id)
    produto_imagem = ImagemProduto.query.filter_by(produto_id=id).all()

    return render_template('produto.html', produto=produto, fotos=produto_imagem)

# =================== Editar Produto ====================
@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    if 'usuario' in session and session.get('tipo') == 'Administrador':
        produto = Produtos.query.get(id)
        imagens = ImagemProduto.query.filter_by(produto_id=id).all()
        if request.method == 'POST':
            nome = request.form.get('nome_produto')
            descricao = request.form.get('descricao')
            preco = request.form.get('preco')

            if not nome or not preco:
                flash("Campos obrigatórios não foram preenchidos!")
                return redirect(request.url)

            produto.nome = nome
            produto.descricao = descricao
            produto.preco = float(preco)

            db.session.commit()

            flash("Produto atualizado com sucesso!")
            return redirect(url_for('admin'))

        return render_template('editar_produto.html', produto=produto, imagens=imagens)
    else:
        return redirect('/')
    
# =================== Rota para adicionar imagens ao produto ===================
@app.route('/admin/editar/<int:id>/adicionar-imagem', methods=['POST'])
def adicionar_imagem_produto(id):
    if 'usuario' in session and session.get('tipo') == 'Administrador':
        produto = Produtos.query.get(id)
        if not produto:
            flash("Produto não encontrado!")
            return redirect(url_for('admin'))

        if 'imagem' not in request.files:
            flash("Nenhuma imagem selecionada!")
            return redirect(request.url)

        imagem_file = request.files['imagem']
        if imagem_file.filename == '':
            flash("Nenhum arquivo selecionado!")
            return redirect(request.url)

        if imagem_file:
            filename = secure_filename(imagem_file.filename)
            caminho_salvar = os.path.join(current_app.root_path, 'static/Img/Produtos', filename)
            imagem_file.save(caminho_salvar)

            nova_imagem = ImagemProduto(
                produto_id=id,
                caminho_imagem=f'Img/Produtos/{filename}'
            )
            db.session.add(nova_imagem)
            db.session.commit()

            flash("Imagem adicionada com sucesso!")
            return redirect(url_for('editar_produto', id=id))
    else:
        return redirect('/')

# ================== Rota para deletar imagens do produto ===================
@app.route('/admin/editar/<int:id>/deletar-imagem/<int:imagem_id>', methods=['POST'])
def deletar_imagem_produto(id, imagem_id):
    if 'usuario' in session and session.get('tipo') == 'Administrador':
        imagem = ImagemProduto.query.get(imagem_id)
        if not imagem:
            flash("Imagem não encontrada!")
            return redirect(url_for('editar_produto', id=id))

        db.session.delete(imagem)
        db.session.commit()

        flash("Imagem deletada com sucesso!")
        return redirect(url_for('editar_produto', id=id))
    else:
        return redirect('/')
    
# =================== Debug ===================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_datas()
    app.run(debug=True)