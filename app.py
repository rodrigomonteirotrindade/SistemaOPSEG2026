from flask import Flask, render_template, request, redirect
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "segredo123"

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

    # usuário padrão
    c.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin','123','admin')")

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
        c.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (u,s))
        user = c.fetchone()
        db.close()

        if user:
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

    db = get_db()
    c = db.cursor()

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

    c.execute("SELECT * FROM registros")
    registros = c.fetchall()

    c.execute("SELECT COUNT(*) FROM registros")
    total = c.fetchone()[0]

    def count(n):
        c.execute("SELECT COUNT(*) FROM registros WHERE nivel=?", (n,))
        return c.fetchone()[0]

    n1, n2, n3, n4 = count("1"), count("2"), count("3"), count("4")

    c.execute("SELECT DISTINCT colaborador FROM registros")
    operadores = [x[0] for x in c.fetchall() if x[0]]

    c.execute("SELECT nome FROM clientes")
    clientes = [x[0] for x in c.fetchall()]

    db.close()

    return render_template("index.html",
        registros=registros,
        total=total,n1=n1,n2=n2,n3=n3,n4=n4,
        operadores=operadores,
        clientes=clientes
    )

# ================= EDITAR NIVEL =================
@app.route("/editar/<int:id>", methods=["POST"])
@login_required
def editar(id):
    novo = request.form["nivel"]

    db = get_db()
    c = db.cursor()
    c.execute("UPDATE registros SET nivel=? WHERE id=?", (novo,id))
    db.commit()
    db.close()

    return redirect("/")

# ================= DELETE =================
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM registros WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect("/")

# ================= GRÁFICO =================
@app.route("/grafico")
@login_required
def grafico():

    operador = request.args.get("operador")

    db = get_db()
    c = db.cursor()

    if operador and operador != "todos":
        c.execute("SELECT nivel FROM registros WHERE colaborador=?", (operador,))
    else:
        c.execute("SELECT nivel FROM registros")

    dados = [0,0,0,0]

    for n in c.fetchall():
        if n[0] == "1": dados[0]+=1
        if n[0] == "2": dados[1]+=1
        if n[0] == "3": dados[2]+=1
        if n[0] == "4": dados[3]+=1

    c.execute("SELECT DISTINCT colaborador FROM registros")
    operadores = [x[0] for x in c.fetchall() if x[0]]

    db.close()

    return render_template("grafico.html", dados=dados, operadores=operadores)

# ================= USUÁRIO =================
@app.route("/usuarios", methods=["GET","POST"])
@login_required
def usuarios():
    if request.method == "POST":
        db = get_db()
        c = db.cursor()
        c.execute("INSERT INTO usuarios VALUES (?,?,?)", (
            request.form["username"],
            request.form["password"],
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
        c.execute("INSERT INTO clientes VALUES (?)", (
            request.form["nome"],
        ))
        db.commit()
        db.close()
        return redirect("/clientes")

    return render_template("clientes.html")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)