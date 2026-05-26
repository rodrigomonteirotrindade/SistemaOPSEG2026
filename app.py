from flask import Flask, render_template, request, redirect
import pandas as pd
import os

app = Flask(__name__)

ARQUIVO_EXCEL = "registros.xlsx"

# CRIAR PLANILHA AUTOMÁTICA
if not os.path.exists(ARQUIVO_EXCEL):

    df = pd.DataFrame(columns=[
        "Data",
        "Cliente",
        "Titulo",
        "Colaborador",
        "Pontuacao",
        "OPSEG"
    ])

    df.to_excel(ARQUIVO_EXCEL, index=False)

@app.route("/", methods=["GET", "POST"])
def dashboard():

    # SALVAR REGISTRO
    if request.method == "POST":

        novo_registro = {

            "Data": request.form["data"],
            "Cliente": request.form["cliente"],
            "Titulo": request.form["titulo"],
            "Colaborador": request.form["colaborador"],
            "Pontuacao": request.form["pontuacao"],
            "OPSEG": request.form["opseg"]

        }

        df = pd.read_excel(ARQUIVO_EXCEL)

        df = pd.concat(
            [df, pd.DataFrame([novo_registro])],
            ignore_index=True
        )

        df.to_excel(ARQUIVO_EXCEL, index=False)

        return redirect("/")

    # LER DADOS
    df = pd.read_excel(ARQUIVO_EXCEL)

    registros = df.to_dict(orient="records")

    # DASHBOARD

    total_registros = len(df)

    media_pontuacao = 0

    if not df.empty:

        try:
            media_pontuacao = round(
                pd.to_numeric(df["Pontuacao"]).mean(),
                2
            )
        except:
            media_pontuacao = 0

    total_colaboradores = df["Colaborador"].nunique()

    total_opseg = df["OPSEG"].nunique()

    # DADOS DO GRÁFICO

    grafico = (
        df.groupby("Colaborador")["Pontuacao"]
        .mean()
        .fillna(0)
    )

    labels = list(grafico.index)

    valores = [
        round(float(v), 2)
        for v in grafico.values
    ]

    return render_template(

        "index.html",

        registros=registros,

        total_registros=total_registros,

        media_pontuacao=media_pontuacao,

        total_colaboradores=total_colaboradores,

        total_opseg=total_opseg,

        labels=labels,

        valores=valores

    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)