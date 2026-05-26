from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "segredo123"
bcrypt = Bcrypt(app)

# ================= BANCO =================
def get_db():
    return sqlite3.connect("banco.db")

def criar_banco():
    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        username TEXT PRIMARY KEY,
        password TEXT,
        tipo TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        nome TEXT PRIMARY KEY
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        titulo TEXT,
        cliente TEXT,
        colaborador TEXT,
        nivel TEXT
    )
    """)

    senha_hash = bcrypt.generate_password_hash("evt123456").decode('utf-8')
    c.execute("INSERT OR IGNORE INTO usuarios VALUES ('Liderseg', ?, 'admin')", (senha_hash,))

    db.commit()
    db.close()

criar_banco()

# ================= LOGIN =================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, username, tipo):
        self.id = username
        self.tipo = tipo

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM usuarios WHERE username=?", (user_id,))
    user = c.fetchone()
    db.close()

    if user:
        return User(user[0], user[2])
    return None

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        s = request.form["password"]

        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM usuarios WHERE username=?", (u,))
        user = c.fetchone()
        db.close()

        if user and bcrypt.check_password_hash(user[1], s):
            login_user(User(user[0], user[2]))
            return redirect("/")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ================= DASHBOARD =================
@app.route("/", methods=["GET","POST"])
@login_required
def index():

    operador_filtro = request.args.get("operador")

    db = get_db()
    c = db.cursor()

    # SALVAR REGISTRO
    if request.method == "POST":
        c.execute("""
        INSERT INTO registros (data,titulo,cliente,colaborador,nivel)
        VALUES (?,?,?,?,?)
        """, (
            request.form["data"],
            request.form["titulo"],
            request.form["cliente"],
            request.form["colaborador"],
            request.form["nivel"]
        ))
        db.commit()
        return redirect("/")

    # FILTRO
    if operador_filtro and operador_filtro != "todos":
        c.execute("SELECT * FROM registros WHERE colaborador=?", (operador_filtro,))
    else:
        c.execute("SELECT * FROM registros")

    registros = c.fetchall()

    total = len(registros)

    def count(n):
        return len([r for r in registros if r[5] == n])

    n1, n2, n3, n4 = count("1"), count("2"), count("3"), count("4")

    # RANKING
    ranking = {}
    for r in registros:
        op = r[4]
        ranking[op] = ranking.get(op, 0) + 1

    ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

    # OPERADORES
    c.execute("SELECT DISTINCT colaborador FROM registros")
    operadores = [x[0] for x in c.fetchall()]

    # CLIENTES
    c.execute("SELECT nome FROM clientes")
    clientes = [x[0] for x in c.fetchall()]

    db.close()

    return render_template("index.html",
        registros=registros,
        total=total,n1=n1,n2=n2,n3=n3,n4=n4,
        ranking=ranking,
        operadores=operadores,
        clientes=clientes,
        operador_filtro=operador_filtro,
        current_user=current_user
    )

# ================= GRÁFICO =================
@app.route("/grafico")
@login_required
def grafico():

    cliente = request.args.get("cliente")

    valores = {"1":1.99,"2":2.99,"3":4.99,"4":7.99}

    db = get_db()
    c = db.cursor()

    if cliente and cliente != "todos":
        c.execute("SELECT nivel FROM registros WHERE cliente=?", (cliente,))
    else:
        c.execute("SELECT nivel FROM registros")

    dados = [0,0,0,0]
    total_valor = 0

    for n in c.fetchall():
        if n[0] == "1":
            dados[0]+=1
            total_valor += valores["1"]
        elif n[0] == "2":
            dados[1]+=1
            total_valor += valores["2"]
        elif n[0] == "3":
            dados[2]+=1
            total_valor += valores["3"]
        elif n[0] == "4":
            dados[3]+=1
            total_valor += valores["4"]

    c.execute("SELECT nome FROM clientes")
    clientes = [x[0] for x in c.fetchall()]

    db.close()

    return render_template("grafico.html",
        dados=dados,
        clientes=clientes,
        total_valor=round(total_valor,2)
    )

# ================= USUÁRIOS =================
@app.route("/usuarios", methods=["GET","POST"])
@login_required
def usuarios():

    if current_user.tipo != "admin":
        return redirect("/")

    if request.method == "POST":
        senha_hash = bcrypt.generate_password_hash(request.form["password"]).decode('utf-8')

        db = get_db()
        c = db.cursor()
        c.execute("INSERT INTO usuarios VALUES (?,?,?)", (
            request.form["username"],
            senha_hash,
            request.form["tipo"]
        ))
        db.commit()
        db.close()

        return redirect("/usuarios")

    return render_template("usuarios.html")

# ================= CLIENTES =================
@app.route("/clientes", methods=["GET","POST"])
@login_required
def clientes():

    if request.method == "POST":
        db = get_db()
        c = db.cursor()
        c.execute("INSERT INTO clientes VALUES (?)", (request.form["nome"],))
        db.commit()
        db.close()
        return redirect("/clientes")

    return render_template("clientes.html")

# ================= EXPORTAR PDF =================
@app.route("/exportar")
@login_required
def exportar():

    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM registros")
    dados = c.fetchall()
    db.close()

    arquivo = "relatorio.pdf"
    pdf = canvas.Canvas(arquivo)

    y = 800
    for r in dados:
        pdf.drawString(50, y, str(r))
        y -= 20

    pdf.save()

    return send_file(arquivo, as_attachment=True)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)