import os
from flask import Flask, render_template, request, redirect, send_file
import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from io import BytesIO
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from openpyxl import Workbook

app = Flask(__name__)
app.secret_key = "troque-esta-chave"

# ================= BANCO =================

def get_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")

    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor
    )

    return conn

def criar_banco():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        username VARCHAR(100) PRIMARY KEY,
        password TEXT,
        tipo TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes(
        nome TEXT PRIMARY KEY
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS registros(
        id SERIAL PRIMARY KEY,
        data TEXT,
        titulo TEXT,
        cliente TEXT,
        colaborador TEXT,
        nivel TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS historico(
    id SERIAL PRIMARY KEY,
        usuario TEXT,
        acao TEXT,
        data_hora TEXT
    )
    """)

    c.execute("""
INSERT INTO usuarios(username,password,tipo)
VALUES ('Liderseg','123','admin')
ON CONFLICT (username) DO NOTHING
""")
    
    conn.commit()
    conn.close()

criar_banco()


def registrar_historico(usuario, acao):
    conn = get_db()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO historico(usuario,acao,data_hora)
        VALUES (%s,%s,%s)
        """,
        (usuario, acao, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    )

    def registrar_historico(usuario, acao):
    conn = get_db()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO historico(usuario,acao,data_hora)
        VALUES (%s,%s,%s)
        """,
        (
            usuario,
            acao,
            datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()

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
    @login_manager.user_loader
def load_user(user_id):

    conn = get_db()
    c = conn.cursor()

    c.execute(
        """
        SELECT *
        FROM usuarios
        WHERE username=%s
        """,
        (user_id,)
    )

    u = c.fetchone()

    conn.close()

    if u:
        return User(
            u["username"],
            u["tipo"]
        )

    return None
    conn.close()

    if u:
        return User(u["username"], u["tipo"])

    return None

def is_admin():
    return current_user.is_authenticated and current_user.tipo == "admin"

# ================= LOGIN =================

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()

        c.execute(
            """
            SELECT *
            FROM usuarios
            WHERE username=%s
            AND password=%s
            """,
            (username, password)
        )

        user = c.fetchone()

        conn.close()

        if user:
            login_user(
                User(
                    user["username"],
                    user["tipo"]
                )
            )

            return redirect("/")

    return render_template("login.html")
# ================= EDITAR =================

@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):

    if not is_admin():
        return "Sem permissão"

    conn = get_db()
    c = conn.cursor()

    c.execute(
    """
    SELECT *
    FROM registros
    WHERE id=%s
    """,
    (id,)
)

registro = c.fetchone()
)

    if not registro:
        conn.close()
        return "Registro não encontrado"

    if request.method == "POST":

        c.execute("""
        UPDATE registros
        SET data=%s,
titulo=%s,
cliente=%s,
colaborador=%s,
nivel=%s
WHERE id=%s
        """, (
            request.form["data"],
            request.form["titulo"],
            request.form["cliente"],
            request.form["colaborador"],
            request.form["nivel"],
            id
        ))

        conn.commit()

        registrar_historico(
            current_user.id,
            f"Editou registro {id}"
        )

        return redirect("/")

    clientes = c.execute(
        "SELECT nome FROM clientes ORDER BY nome"
    ).fetchall()

    conn.close()

    return render_template(
        "editar.html",
        r=registro,
        clientes=[x["nome"] for x in clientes],
        is_admin=True
    )

# ================= EXCLUIR =================

@app.route("/excluir/<int:id>")
@login_required
def excluir(id):

    if not is_admin():
        return "Sem permissão"

    conn = get_db()

   c = conn.cursor()

c.execute(
    """
    DELETE
    FROM registros
    WHERE id=%s
    """,
    (id,)
)

    conn.commit()
    conn.close()

    registrar_historico(
        current_user.id,
        f"Excluiu registro {id}"
    )

    return redirect("/")

# ================= CLIENTES =================

@app.route("/clientes", methods=["GET", "POST"])
@login_required
def clientes():

    if not is_admin():
        return "Acesso negado"

    conn = get_db()

    if request.method == "POST":
        try:
            c = conn.cursor()

c.execute(
    """
    INSERT INTO clientes(nome)
    VALUES (%s)
    """,
    (request.form["nome"],)
)
                (request.form["nome"],)
            )
            conn.commit()

            registrar_historico(
                current_user.id,
                f"Criou cliente {request.form['nome']}"
            )
        except:
            pass

    lista = conn.execute(
        "SELECT * FROM clientes ORDER BY nome"
    ).fetchall()

    conn.close()

    return render_template(
        "clientes.html",
        clientes=lista
    )

# ================= USUÁRIOS =================

@app.route("/usuarios", methods=["GET", "POST"])
@login_required
def usuarios():

    if not is_admin():
        return "Acesso negado"

    conn = get_db()

    if request.method == "POST":
        try:
            conn.execute(
                c = conn.cursor()

c.execute(
    """
    INSERT INTO usuarios
    VALUES (%s,%s,%s)
    """,
    (
        request.form["username"],
        request.form["password"],
        request.form["tipo"]
    )

                (
                    request.form["username"],
                    request.form["password"],
                    request.form["tipo"]
                )
            )
            conn.commit()

            registrar_historico(
                current_user.id,
                f"Criou usuário {request.form['username']}"
            )
        except:
            pass

    lista = conn.execute(
        "SELECT username,tipo FROM usuarios ORDER BY username"
    ).fetchall()

    conn.close()

    return render_template(
        "usuarios.html",
        usuarios=lista
    )
@app.route("/editar_usuario/<username>", methods=["GET", "POST"])
@login_required
def editar_usuario(username):

    if not is_admin():
        return "Acesso negado"

    conn = get_db()

    usuario = conn.execute(
        "SELECT * FROM usuarios WHERE username=%s",
        (username,)
    ).fetchone()

    if not usuario:
        conn.close()
        return redirect("/usuarios")

    if request.method == "POST":

        conn.execute("""
        UPDATE usuarios
        SET password=?, tipo=?
        WHERE username=%s
        """,
        (
            request.form["password"],
            request.form["tipo"],
            username
        ))

        conn.commit()

        registrar_historico(
            current_user.id,
            f"Editou usuário {username}"
        )

        conn.close()

        return redirect("/usuarios")

    conn.close()

    return render_template(
        "editar_usuario.html",
        usuario=usuario
    )
@app.route("/excluir_usuario/<username>")
@login_required
def excluir_usuario(username):

    if not is_admin():
        return "Acesso negado"

    if username == current_user.id:
        return "Não é permitido excluir seu próprio usuário."

    conn = get_db()

    conn.execute(
        "DELETE FROM usuarios WHERE username=%s",
        (username,)
    )

    conn.commit()
    conn.close()

    registrar_historico(
        current_user.id,
        f"Excluiu usuário {username}"
    )

    return redirect("/usuarios")
@app.route("/editar_cliente/<nome>", methods=["GET", "POST"])
@login_required
def editar_cliente(nome):

    if not is_admin():
        return "Acesso negado"

    conn = get_db()

    cliente = conn.execute(
        "SELECT * FROM clientes WHERE nome=?",
        (nome,)
    ).fetchone()

    if not cliente:
        conn.close()
        return redirect("/clientes")

    if request.method == "POST":

        novo_nome = request.form["nome"]

        conn.execute(
            "UPDATE clientes SET nome=? WHERE nome=?",
            (novo_nome, nome)
        )

        conn.commit()

        registrar_historico(
            current_user.id,
            f"Editou cliente {nome}"
        )

        conn.close()

        return redirect("/clientes")

    conn.close()

    return render_template(
        "editar_cliente.html",
        cliente=cliente
    )
@app.route("/excluir_cliente/<nome>")
@login_required
def excluir_cliente(nome):

    if not is_admin():
        return "Acesso negado"

    conn = get_db()

    conn.execute(
        "DELETE FROM clientes WHERE nome=?",
        (nome,)
    )

    conn.commit()
    conn.close()

    registrar_historico(
        current_user.id,
        f"Excluiu cliente {nome}"
    )

    return redirect("/clientes")
# ================= RANKING =================

@app.route("/ranking")
@login_required
def ranking():

    conn = get_db()

    ranking = conn.execute("""
    SELECT colaborador, COUNT(*) total
    FROM registros
    GROUP BY colaborador
    ORDER BY total DESC
    """).fetchall()

    conn.close()

    return render_template("ranking.html", ranking=ranking)

# ================= HISTÓRICO =================

@app.route("/historico")
@login_required
def historico():

    if not is_admin():
        return "Acesso negado"

    conn = get_db()

    dados = conn.execute("""
    SELECT *
    FROM historico
    ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "historico.html",
        historico=dados
    )

# ================= EXCEL =================

@app.route("/exportar_excel")
@login_required
def exportar_excel():

    conn = get_db()

    if is_admin():
        registros = conn.execute(
            "SELECT * FROM registros ORDER BY id DESC"
        ).fetchall()
    else:
        registros = conn.execute(
            "SELECT * FROM registros WHERE colaborador=? ORDER BY id DESC",
            (current_user.id,)
        ).fetchall()

    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Registros"

    ws.append([
        "ID",
        "Data",
        "Título",
        "Cliente",
        "Operador",
        "Nível"
    ])

    for r in registros:
        ws.append([
            r["id"],
            r["data"],
            r["titulo"],
            r["cliente"],
            r["colaborador"],
            r["nivel"]
        ])

    arquivo = BytesIO()
    wb.save(arquivo)
    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="registros.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ================= ALTERAR SENHA =================

@app.route("/alterar_senha/<username>", methods=["POST"])
@login_required
def alterar_senha(username):

    if not is_admin():
        return "Sem permissão"

    nova=request.form["nova_senha"]

    conn=get_db()
    c=conn.cursor()

    c.execute("""
    UPDATE usuarios
    SET password=?
    WHERE username=%s
    """,(nova,username))

    conn.commit()
    conn.close()

    return redirect("/usuarios")
# ================= GRAFICO =================

@app.route("/grafico")
@login_required
def grafico():

    conn = get_db()
    c = conn.cursor()

    operador = request.args.get("operador","todos")

    # ADMIN → pode ver tudo + escolher operador
    if is_admin():

        if operador == "todos":

            c.execute("""
            SELECT * FROM registros
            """)

        else:

            c.execute("""
            SELECT * FROM registros
            WHERE colaborador=?
            """,(operador,))

    # OPERADOR → vê somente o próprio

    else:

        operador = current_user.id

        c.execute("""
        SELECT * FROM registros
        WHERE colaborador=?
        """,(current_user.id,))

    dados = c.fetchall()

    # CONTAGEM

    n1=len([x for x in dados if x["nivel"]=="1"])
    n2=len([x for x in dados if x["nivel"]=="2"])
    n3=len([x for x in dados if x["nivel"]=="3"])
    n4=len([x for x in dados if x["nivel"]=="4"])

    # VALORES

    v1=n1*1.99
    v2=n2*2.99
    v3=n3*4.99
    v4=n4*7.99

    total=round(v1+v2+v3+v4,2)

    # LISTA OPERADORES

    operadores=[]

    if is_admin():

        c.execute("""
        SELECT DISTINCT colaborador
        FROM registros
        ORDER BY colaborador
        """)

        operadores=[x["colaborador"] for x in c.fetchall()]

    conn.close()

    return render_template(
        "grafico.html",

        n1=n1,
        n2=n2,
        n3=n3,
        n4=n4,

        v1=round(v1,2),
        v2=round(v2,2),
        v3=round(v3,2),
        v4=round(v4,2),

        total=total,

        operadores=operadores,
        operador_selecionado=operador,

        is_admin=is_admin()
    )

if __name__ == "__main__":
    app.run(debug=True)
