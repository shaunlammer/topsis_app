from flask import Blueprint, render_template, request, redirect, url_for, session
import numpy as np

routes = Blueprint('routes', __name__)

# Historial de ejemplo
historial = [
    {"fecha": "2025-11-01", "criterios": 6, "resultado": "Inf: 0.3, Eco: 0.2, ..."},
    {"fecha": "2025-10-28", "criterios": 4, "resultado": "Eco: 0.4, Rh: 0.3, ..."}
]

# --------------------------
# HOME
# --------------------------
@routes.route("/")
def index():
    return render_template("home.html", historial=historial)


# --------------------------
# SELECCIÓN DE NÚMERO DE CRITERIOS
# --------------------------
@routes.route("/select_size", methods=["POST"])
def select_size():
    num = request.form.get("num_criterios")

    if not num:
        return redirect(url_for("routes.index"))

    session["num_criterios"] = int(num)
    return redirect(url_for("routes.assign_names"))


# --------------------------
# ASIGNAR NOMBRES DE CRITERIOS
# --------------------------
@routes.route("/assign", methods=["GET", "POST"])
def assign_names():
    num = session.get("num_criterios")

    if num is None:
        return redirect(url_for("routes.index"))

    if request.method == "POST":
        criterios = [request.form[f"criterio_{i}"] for i in range(num)]
        tipos = [request.form.get(f"tipo_{i}", "max") for i in range(num)]

        session["criterios"] = criterios
        session["tipos"] = tipos

        return redirect(url_for("routes.matriz"))

    return render_template("assign_names.html", num_criterios=num)


# --------------------------
# MATRIZ AHP
# --------------------------
@routes.route("/matriz", methods=["GET", "POST"])
def matriz():
    num = session.get("num_criterios")
    criterios = session.get("criterios")

    if num is None or criterios is None:
        return redirect(url_for("routes.index"))

    if request.method == "POST":
        matriz = np.zeros((num, num))

        for i in range(num):
            for j in range(num):
                entrada = request.form[f"cell_{i}_{j}"]
                try:
                    valor = float(entrada)
                    if valor <= 0:
                        raise ValueError
                    matriz[i][j] = valor
                except:
                    matriz[i][j] = 1.0 if i == j else 0.0

        valores, vectores = np.linalg.eig(matriz)
        indice_max = np.argmax(valores.real)
        vector_eigen = vectores[:, indice_max].real
        pesos = vector_eigen / np.sum(vector_eigen)

        session["pesos"] = pesos.tolist()

        return render_template("resultado.html", criterios=criterios, pesos=np.round(pesos, 4))

    return render_template("matriz.html", num_criterios=num, criterios=criterios)


# --------------------------
# NÚMERO DE ALTERNATIVAS
# --------------------------
@routes.route("/alternativas", methods=["GET", "POST"])
def alternativas():
    criterios = session.get("criterios")

    if criterios is None:
        return redirect(url_for("routes.index"))

    if request.method == "POST":
        num_alt = int(request.form["num_alternativas"])
        session["num_alternativas"] = num_alt
        return redirect(url_for("routes.nombres_alternativas"))

    return render_template("alternativas.html", criterios=criterios)


# --------------------------
# NOMBRES DE ALTERNATIVAS
# --------------------------
@routes.route("/nombres_alternativas", methods=["GET", "POST"])
def nombres_alternativas():
    num_alt = session.get("num_alternativas")

    if num_alt is None:
        return redirect(url_for("routes.alternativas"))

    if request.method == "POST":
        alternativas = [request.form[f"alternativa_{i}"] for i in range(num_alt)]
        session["alternativas"] = alternativas
        return redirect(url_for("routes.evaluacion"))

    return render_template("nombres_alternativas.html", num_alternativas=num_alt)


# --------------------------
# MATRIZ DE EVALUACIÓN TOPSIS
# --------------------------
@routes.route("/evaluacion", methods=["GET", "POST"])
def evaluacion():
    criterios = session.get("criterios")
    alternativas = session.get("alternativas")

    if criterios is None or alternativas is None:
        return redirect(url_for("routes.index"))

    num_alt = len(alternativas)
    num_crit = len(criterios)

    if request.method == "POST":
        matriz = np.zeros((num_alt, num_crit))

        for i in range(num_alt):
            for j in range(num_crit):
                valor = float(request.form[f"cell_{i}_{j}"])
                matriz[i][j] = valor

        session["matriz_evaluacion"] = matriz.tolist()
        return redirect(url_for("routes.topsis"))

    return render_template("evaluacion.html", criterios=criterios, alternativas=alternativas)


# --------------------------
# TOPSIS
# --------------------------
@routes.route("/topsis")
def topsis():
    criterios = session.get("criterios")
    alternativas = session.get("alternativas")
    matriz = session.get("matriz_evaluacion")
    pesos = session.get("pesos")
    tipos = session.get("tipos")

    if None in (criterios, alternativas, matriz, pesos, tipos):
        return redirect(url_for("routes.index"))

    matriz = np.array(matriz, dtype=float)
    pesos = np.array(pesos, dtype=float)

    denominadores = np.sqrt(np.sum(matriz**2, axis=0))
    matriz_norm = matriz / denominadores
    matriz_pond = matriz_norm * pesos

    ideal_pos = np.array([
        np.max(matriz_pond[:, j]) if tipos[j] == 'max' else np.min(matriz_pond[:, j])
        for j in range(len(tipos))
    ])
    ideal_neg = np.array([
        np.min(matriz_pond[:, j]) if tipos[j] == 'max' else np.max(matriz_pond[:, j])
        for j in range(len(tipos))
    ])

    dist_pos = np.sqrt(np.sum((matriz_pond - ideal_pos)**2, axis=1))
    dist_neg = np.sqrt(np.sum((matriz_pond - ideal_neg)**2, axis=1))

    puntuaciones = dist_neg / (dist_pos + dist_neg)
    ranking = np.argsort(-puntuaciones)

    resultados = [(alternativas[i], round(puntuaciones[i], 4)) for i in ranking]

    return render_template("topsis_resultado.html", resultados=resultados)
