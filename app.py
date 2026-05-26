from flask import Flask, render_template, request, redirect
import pandas as pd
import os

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "segredo123"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# USERS
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

arquivo = "registros.xlsx"
colunas = ["Data", "Cliente", "Colaborador", "Nivel"]

# CRIA / CORRIGE EXCEL
if not os.path.exists(arquivo):
    df = pd.DataFrame(columns=colunas)
    df.to_excel(arquivo, index=False)

def carregar_df():
    df = pd.read_excel(arquivo)

    # LIMPEZA IMPORTANTE (resolve seu problema)
    df["Nivel"] = df["Nivel"].astype(str).str.replace(".0", "", regex=False)
    df = df.fillna("")

    return df

# LOGIN
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

# DELETE
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    df = carregar_df()
    df = df.drop(id)
    df.to_excel(arquivo, index=False)
    return redirect("/")

# DASHBOARD
@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    if request.method == "POST":
        df = carregar_df()

        novo = pd.DataFrame([[
            request.form["data"],
            request.form["cliente"],
            request.form["colaborador"],
            request.form["nivel"]
        ]], columns=df.columns)

        df = pd.concat([df, novo], ignore_index=True)
        df.to_excel(arquivo, index=False)

        return redirect("/")

    df = carregar_df()
    registros = df.to_dict(orient="records")

    # CONTADORES CORRETOS
    total = len(df)
    n1 = len(df[df["Nivel"] == "1"])
    n2 = len(df[df["Nivel"] == "2"])
    n3 = len(df[df["Nivel"] == "3"])
    n4 = len(df[df["Nivel"] == "4"])

    operadores = sorted(df["Colaborador"].unique())

    return render_template(
        "index.html",
        registros=registros,
        total=total,
        n1=n1,
        n2=n2,
        n3=n3,
        n4=n4,
        tipo=current_user.tipo,
        operadores=operadores
    )

# GRÁFICO COM FILTRO
@app.route("/grafico", methods=["GET"])
@login_required
def grafico():

    operador = request.args.get("operador")

    df = carregar_df()

    if operador and operador != "todos":
        df = df[df["Colaborador"] == operador]

    contagem = df["Nivel"].value_counts().to_dict()

    dados = {
        "1": contagem.get("1", 0),
        "2": contagem.get("2", 0),
        "3": contagem.get("3", 0),
        "4": contagem.get("4", 0),
    }

    operadores = sorted(df["Colaborador"].unique())

    return render_template("grafico.html", dados=dados, operadores=operadores, operador=operador)

# RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)