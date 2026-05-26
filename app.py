from flask import Flask, render_template, request, redirect
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "segredo123"
bcrypt = Bcrypt(app)

# ================= BANCO =================
def get_db():
    return sqlite3.connect("banco.db")

def criar_banco():
    with get_db() as db:
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
    with get_db() as db:
        c = db.cursor()
        c.execute("SELECT * FROM usuarios WHERE username=?", (user_id,))
        user = c.fetchone()

    if user:
        return User(user[0], user[2])
    return None

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        s = request.form["password"]

        with get_db() as db:
            c = db.cursor()
            c.execute("SELECT * FROM usuarios WHERE username=?", (u,))
            user = c.fetchone()

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
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    # SALVAR
    if request.method == "POST":
        with get_db() as db:
            c = db.cursor()
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
        return redirect("/")

    with get_db() as db:
        c = db.cursor()

        query = "SELECT * FROM registros WHERE 1=1"
        params = []

        if operador_filtro and operador_filtro != "todos":
            query += " AND colaborador=?"
            params.append(operador_filtro)

        if data_inicio:
            query += " AND data >= ?"
            params.append(data_inicio)

        if data_fim:
            query += " AND data <= ?"
            params.append(data_fim)

        c.execute(query, params)
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

    return render_template("index.html",
        registros=registros,
        total=total,n1=n1,n2=n2,n3=n3,n4=n4,
        ranking=ranking,
        operadores=operadores,
        clientes=clientes,
        operador_filtro=operador_filtro,
        data_inicio=data_inicio,
        data_fim=data_fim,
        current_user=current_user
    )

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)