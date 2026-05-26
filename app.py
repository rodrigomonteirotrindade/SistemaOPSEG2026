from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os

# LOGIN
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.secret_key = "segredo123"  # pode trocar depois

# CONFIG LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# USUÁRIO FIXO
class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {
    "liderseg": {"password": "evt123456"}
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ARQUIVO EXCEL
arquivo = "registros.xlsx"

# CRIA EXCEL SE NÃO EXISTIR
if not os.path.exists(arquivo):
    df = pd.DataFrame(columns=["Data", "Cliente", "Colaborador"])
    df.to_excel(arquivo, index=False)

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for("index"))

    return render_template("login.html")

# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# TELA PRINCIPAL (PROTEGIDA)
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        data = request.form["data"]
        cliente = request.form["cliente"]
        colaborador = request.form["colaborador"]

        df = pd.read_excel(arquivo)
        novo = pd.DataFrame([[data, cliente, colaborador]], columns=df.columns)
        df = pd.concat([df, novo], ignore_index=True)
        df.to_excel(arquivo, index=False)

        return redirect("/")

    df = pd.read_excel(arquivo)
    registros = df.to_dict(orient="records")

    return render_template("index.html", registros=registros)

# RENDER (PORTA CORRETA)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
# login ativado