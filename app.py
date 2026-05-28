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

    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        username TEXT PRIMARY KEY,
        password TEXT,
        tipo TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS clientes (
        nome TEXT PRIMARY KEY
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        titulo TEXT,
        cliente TEXT,
        colaborador TEXT,
        nivel TEXT
    )""")

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

def is_admin():
    return current_user.tipo == "admin"

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        s = request.form["password"]

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

    # 🔥 OPERADOR SÓ VÊ OS DELE
    if is_admin():
        c.execute("SELECT * FROM registros ORDER BY id DESC")
    else:
        c.execute("SELECT * FROM registros WHERE colaborador=? ORDER BY id DESC", (current_user.id,))

    registros = c.fetchall()

    # INSERT
    if request.method == "POST":
        c.execute("""
        INSERT INTO registros (data,titulo,cliente,colaborador,nivel)
        VALUES (?,?,?,?,?)
        """, (
            request.form["data"],
            request.form["titulo"],
            request.form["cliente"],
            current_user.id if not is_admin() else request.form["colaborador"],
            request.form["nivel"]
        ))
        conn.commit()
        return redirect("/")

    c.execute("SELECT nome FROM clientes")
    clientes = [x["nome"] for x in c.fetchall()]

    conn.close()

    return render_template("index.html",
        registros=registros,
        clientes=clientes,
        is_admin=is_admin(),
        usuario=current_user.id
    )

# ================= EDITAR =================
@app.route("/editar/<int:id>", methods=["GET","POST"])
@login_required
def editar(id):

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM registros WHERE id=?", (id,))
    r = c.fetchone()

    if not r:
        return "Registro não encontrado"

    # 🔒 OPERADOR NÃO PODE EDITAR OUTROS
    if not is_admin() and r["colaborador"] != current_user.id:
        return "Sem permissão"

    if request.method == "POST":
        c.execute("""
        UPDATE registros SET
        data=?, titulo=?, cliente=?, colaborador=?, nivel=?
        WHERE id=?
        """, (
            request.form["data"],
            request.form["titulo"],
            request.form["cliente"],
            request.form["colaborador"],
            request.form["nivel"],
            id
        ))
        conn.commit()
        conn.close()
        return redirect("/")

    c.execute("SELECT nome FROM clientes")
    clientes = [x["nome"] for x in c.fetchall()]

    conn.close()

    return render_template("editar.html", r=r, clientes=clientes, is_admin=is_admin())

# ================= EXCLUIR =================
@app.route("/excluir/<int:id>")
@login_required
def excluir(id):

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM registros WHERE id=?", (id,))
    r = c.fetchone()

    if not r:
        return "Erro"

    if not is_admin() and r["colaborador"] != current_user.id:
        return "Sem permissão"

    c.execute("DELETE FROM registros WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

# ================= GRÁFICO =================
@app.route("/grafico")
@login_required
def grafico():

    conn = get_db()
    c = conn.cursor()

    # 🔥 FILTRO AUTOMÁTICO POR USUÁRIO
    if is_admin():
        c.execute("SELECT * FROM registros")
    else:
        c.execute("SELECT * FROM registros WHERE colaborador=?", (current_user.id,))

    dados = c.fetchall()

    n1 = len([x for x in dados if x["nivel"] == "1"])
    n2 = len([x for x in dados if x["nivel"] == "2"])
    n3 = len([x for x in dados if x["nivel"] == "3"])
    n4 = len([x for x in dados if x["nivel"] == "4"])

    # 💰 VALORES
    total = (n1*1.99)+(n2*2.99)+(n3*4.99)+(n4*7.99)

    conn.close()

    return render_template("grafico.html",
        n1=n1,n2=n2,n3=n3,n4=n4,
        total=total,
        usuario=current_user.id
    )

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)