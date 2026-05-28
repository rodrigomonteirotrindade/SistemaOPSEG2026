from flask import Flask, render_template, request, redirect
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "segredo123"

# ================= BANCO =================
def get_db():
    conn = sqlite3.connect("banco.db")
    conn.row_factory = sqlite3.Row
    return conn

def criar_banco():
    conn = get_db()
    c = conn.cursor()

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

    c.execute("INSERT OR IGNORE INTO usuarios VALUES ('Liderseg','evt123456','admin')")

    conn.commit()
    conn.close()

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
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE username=?", (user_id,))
    user = c.fetchone()
    conn.close()

    if user:
        return User(user["username"], user["tipo"])
    return None

def is_admin():
    return current_user.tipo == "admin"

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        s = request.form.get("password")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (u,s))
        user = c.fetchone()
        conn.close()

        if user:
            login_user(User(user["username"], user["tipo"]))
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

    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        c.execute("""
        INSERT INTO registros (data,titulo,cliente,colaborador,nivel)
        VALUES (?,?,?,?,?)
        """, (
            request.form.get("data"),
            request.form.get("titulo"),
            request.form.get("cliente"),
            request.form.get("colaborador"),
            request.form.get("nivel")
        ))
        conn.commit()

    c.execute("SELECT * FROM registros ORDER BY id DESC")
    registros = c.fetchall()

    c.execute("SELECT nome FROM clientes")
    clientes = [x["nome"] for x in c.fetchall()]

    conn.close()

    return render_template("index.html",
        registros=registros,
        clientes=clientes,
        is_admin=is_admin()
    )

# ================= EXCLUIR =================
@app.route("/excluir/<int:id>")
@login_required
def excluir(id):

    if not is_admin():
        return "Acesso negado"

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM registros WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

# ================= EDITAR =================
@app.route("/editar/<int:id>", methods=["GET","POST"])
@login_required
def editar(id):

    if not is_admin():
        return "Acesso negado"

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM registros WHERE id=?", (id,))
    r = c.fetchone()

    if r is None:
        conn.close()
        return f"Erro: ID {id} não encontrado"

    r = dict(r)

    if request.method == "POST":
        data = request.form.get("data")
        titulo = request.form.get("titulo")
        cliente = request.form.get("cliente")
        colaborador = request.form.get("colaborador")
        nivel = request.form.get("nivel")

        c.execute("""
        UPDATE registros SET
        data=?, titulo=?, cliente=?, colaborador=?, nivel=?
        WHERE id=?
        """, (data, titulo, cliente, colaborador, nivel, id))

        conn.commit()
        conn.close()
        return redirect("/")

    c.execute("SELECT nome FROM clientes")
    clientes = [x["nome"] for x in c.fetchall()]

    conn.close()

    return render_template("editar.html", r=r, clientes=clientes)

# ================= CLIENTES =================
@app.route("/clientes", methods=["GET","POST"])
@login_required
def clientes():

    if not is_admin():
        return "Acesso negado"

    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        nome = request.form.get("nome")
        if nome:
            c.execute("INSERT INTO clientes VALUES (?)", (nome,))
            conn.commit()

    c.execute("SELECT * FROM clientes")
    lista = c.fetchall()

    conn.close()
    return render_template("clientes.html", clientes=lista)

# ================= USUÁRIOS =================
@app.route("/usuarios", methods=["GET","POST"])
@login_required
def usuarios():

    if not is_admin():
        return "Acesso negado"

    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        tipo = request.form.get("tipo")

        if username and password and tipo:
            c.execute("INSERT INTO usuarios VALUES (?,?,?)",
                      (username, password, tipo))
            conn.commit()

    c.execute("SELECT * FROM usuarios")
    lista = c.fetchall()

    conn.close()
    return render_template("usuarios.html", usuarios=lista)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)