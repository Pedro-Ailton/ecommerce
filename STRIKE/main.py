from flask import Flask, render_template, request, redirect, session, url_for, flash, current_app
from models import Produtos, Fotos, Categorias, Estoque, Clientes, Enderecos, Admins, cadastrar_admin
from db import db
import os
from dotenv import load_dotenv, dotenv_values 
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# =================== Conexão com o banco de dados ===================

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB")
db.init_app(app)

# =================== Página inicial ===================

@app.route('/')
def index():
    banners = ['Img/BANNER-1.png']
    if 'usuario' in session and session.get('tipo') == 'Cliente':
        cliente = Clientes.query.filter_by(email=session['usuario']).first()
        
        nome_usuario = cliente.nome if cliente else 'Usuário Desconhecido'
        produtos = db.session.execute(db.select(Produtos)).scalars().all()
        return render_template('index.html', usuario=session['usuario'], produtos=produtos, nome_usuario=nome_usuario)
    else:
        produtos = db.session.execute(db.select(Produtos)).scalars().all()
        return render_template('index.html',produtos=produtos,banners = banners)


# =================== Página do Produto ====================

@app.route('/produto/<int:id>')
def produto(id):
    sapato = db.session.execute(db.select(Produtos).filter_by(id=id)).scalar.one
    return render_template('produto.html', sapato=sapato)

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
        
        # Buscar administrador pelo email
        administrador = Admins.query.filter_by(email=session['usuario']).first()
        
        imagens = ['Img/banner1.jpg', 'Img/banner2.jpg', 'Img/banner3.jpg']
        nome_usuario = administrador.nome if administrador else 'Usuário Desconhecido'
        
        return render_template('admin.html', 
                             usuario=session['usuario'], 
                             produtos=produtos, 
                             Img=imagens, 
                             nome_usuario=nome_usuario)
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
            imagem = request.files.get('imagem')

            if not nome or not preco or not imagem:
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

            flash("Produto adicionado com sucesso!")
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


# =================== Cadastro de clientes e administradores ===================

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
# =================== Debug ===================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        cadastrar_admin()
    app.run(debug=True)