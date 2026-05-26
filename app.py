from flask import Flask, render_template, request, redirect
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "segredo123"
bcrypt = Bcrypt(app)

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

    senha_hash = bcrypt.generate_password_hash("evt123456").decode('utf-8')

    c.execute("""
    INSERT OR IGNORE INTO usuarios (username,password,tipo)
    VALUES ('Liderseg', ?, 'admin')
    """, (senha_hash,))

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

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        s = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE username=?", (u,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user["password"], s):
            login_user(User(user["username"], user["tipo"]))
            return redirect("/")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ================= EXCLUIR =================
@app.route("/excluir/<int:id>")
@login_required
def excluir(id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM registros WHERE id=?", (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print("ERRO EXCLUIR:", e)

    return redirect("/")

# ================= DASHBOARD =================
@app.route("/", methods=["GET","POST"])
@login_required
def index():

    try:
        # SALVAR
        if request.method == "POST":
            conn = get_db()
            c = conn.cursor()

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

            conn.commit()
            conn.close()

            return redirect("/")

        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT * FROM registros ORDER BY id DESC")
        registros = c.fetchall()

        total = len(registros)

        n1 = len([r for r in registros if r["nivel"] == "1"])
        n2 = len([r for r in registros if r["nivel"] == "2"])
        n3 = len([r for r in registros if r["nivel"] == "3"])
        n4 = len([r for r in registros if r["nivel"] == "4"])

        total_valor = (
            n1*1.99 +
            n2*2.99 +
            n3*4.99 +
            n4*7.99
        )

        # OPERADORES
        operadores = list(set([r["colaborador"] for r in registros]))

        # CLIENTES
        c.execute("SELECT nome FROM clientes")
        clientes = [x["nome"] for x in c.fetchall()]

        conn.close()

        return render_template("index.html",
            registros=registros,
            total=total,
            n1=n1,n2=n2,n3=n3,n4=n4,
            total_valor=round(total_valor,2),
            operadores=operadores,
            clientes=clientes
        )

    except Exception as e:
        return f"ERRO NO SISTEMA: {e}"

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)