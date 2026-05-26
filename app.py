from flask import Flask, render_template, request, redirect
import pandas as pd
import os

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "segredo123"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ================= USUÁRIOS =================
users = {
    "liderseg": {"password": "evt123456", "tipo": "admin"},
    "operador1": {"password": "123", "tipo": "operador"}
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.tipo = users[id]["tipo"]

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ================= EXCEL =================
arquivo = "registros.xlsx"

if not os.path.exists(arquivo):
    df = pd.DataFrame(columns=["Data", "Cliente", "Colaborador", "Nivel"])
    df.to_excel(arquivo, index=False)

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        senha = request.form["password"]

        if user in users and users[user]["password"] == senha:
            login_user(User(user))
            return redirect("/")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ================= CADASTRO USUÁRIO =================
@app.route("/criar_usuario", methods=["GET", "POST"])
@login_required
def criar_usuario():
    if current_user.tipo != "admin":
        return "Acesso negado"

    if request.method == "POST":
        u = request.form["usuario"]
        s = request.form["senha"]
        t = request.form["tipo"]

        users[u] = {"password": s, "tipo": t}
        return redirect("/")

    return render_template("criar_usuario.html")

# ================= DELETE =================
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    df = pd.read_excel(arquivo)
    df = df.drop(id)
    df.to_excel(arquivo, index=False)
    return redirect("/")

# ================= GRÁFICO =================
@app.route("/grafico")
@login_required
def grafico():
    df = pd.read_excel(arquivo)

    dados = df["Nivel"].value_counts().to_dict()

    return render_template("grafico.html", dados=dados)

# ================= HOME =================
@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    if request.method == "POST":
        data = request.form["data"]
        cliente = request.form["cliente"]
        colaborador = request.form["colaborador"]
        nivel = request.form["nivel"]

        df = pd.read_excel(arquivo)
        novo = pd.DataFrame([[data, cliente, colaborador, nivel]], columns=df.columns)
        df = pd.concat([df, novo], ignore_index=True)
        df.to_excel(arquivo, index=False)

        return redirect("/")

    df = pd.read_excel(arquivo)
    registros = df.to_dict(orient="records")

    return render_template("index.html", registros=registros, tipo=current_user.tipo)

# ================= RENDER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)