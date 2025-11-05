from flask import Flask, render_template, request, redirect, url_for, session
import numpy as np

app = Flask(__name__)
app.secret_key = "ahp_secret"
historial = [
    {"fecha": "2025-11-01", "criterios": 6, "resultado": "Inf: 0.3, Eco: 0.2, ..."},
    {"fecha": "2025-10-28", "criterios": 4, "resultado": "Eco: 0.4, Rh: 0.3, ..."}
]

@app.route('/')
def index():
    return render_template('home.html', historial=historial)


@app.route("/", methods=["GET", "POST"])
def select_size():
    if request.method == "POST":
        session["num_criterios"] = int(request.form["num_criterios"])
        return redirect(url_for("assign_names"))
    return render_template("select_size.html")

@app.route("/assign", methods=["GET", "POST"])
def assign_names():
    num = session.get("num_criterios")
    if request.method == "POST":
        criterios = [request.form[f"criterio_{i}"] for i in range(num)]
        tipos = [request.form.get(f"tipo_{i}", "max") for i in range(num)]  # default 'max'
        session["criterios"] = criterios
        session["tipos"] = tipos
        return redirect(url_for("matriz"))
    return render_template("assign_names.html", num_criterios=num)

@app.route("/matriz", methods=["GET", "POST"])
def matriz():
    num = session.get("num_criterios")
    criterios = session.get("criterios")
    if request.method == "POST":
        matriz = np.zeros((num, num))
        for i in range(num):
            for j in range(num):
                entrada = request.form[f"cell_{i}_{j}"]
                try:
                    valor = eval(entrada)
                    if valor <= 0:
                        raise ValueError
                    matriz[i][j] = valor
                except:
                    matriz[i][j] = 1.0 if i == j else 0.0

        # Calcular autovalores y autovectores
        valores, vectores = np.linalg.eig(matriz)
        indice_max = np.argmax(valores.real)
        vector_eigen = vectores[:, indice_max].real
        pesos = vector_eigen / np.sum(vector_eigen)
        session["pesos"] = pesos.tolist()

        return render_template("resultado.html", criterios=criterios, pesos=np.round(pesos, 4))

    return render_template("matriz.html", num_criterios=num, criterios=criterios)
@app.route("/alternativas", methods=["GET", "POST"])
def alternativas():
    criterios = session.get("criterios")
    if request.method == "POST":
        num_alt = int(request.form["num_alternativas"])
        session["num_alternativas"] = num_alt
        return redirect(url_for("nombres_alternativas"))
    return render_template("alternativas.html", criterios=criterios)

@app.route("/nombres_alternativas", methods=["GET", "POST"])
def nombres_alternativas():
    num_alt = session.get("num_alternativas")
    if request.method == "POST":
        alternativas = [request.form[f"alternativa_{i}"] for i in range(num_alt)]
        session["alternativas"] = alternativas
        return redirect(url_for("evaluacion"))
    return render_template("nombres_alternativas.html", num_alternativas=num_alt)

@app.route("/evaluacion", methods=["GET", "POST"])
def evaluacion():
    criterios = session.get("criterios")
    alternativas = session.get("alternativas")
    num_alt = len(alternativas)
    num_crit = len(criterios)
    if request.method == "POST":
        matriz = np.zeros((num_alt, num_crit))
        for i in range(num_alt):
            for j in range(num_crit):
                valor = float(request.form[f"cell_{i}_{j}"])
                matriz[i][j] = valor
        session["matriz_evaluacion"] = matriz.tolist()
        return redirect(url_for("topsis"))
    return render_template("evaluacion.html", criterios=criterios, alternativas=alternativas)

@app.route("/topsis")
def topsis():
    criterios = session.get("criterios")
    alternativas = session.get("alternativas")
    matriz = np.array(session.get("matriz_evaluacion"), dtype=float)
    pesos = session.get("pesos")
    tipos = session.get("tipos", ['max'] * len(criterios))

    if pesos is None:
        return "Error: No se encontraron los pesos AHP en la sesión. Regresa y completa la matriz AHP primero."

    pesos = np.array(pesos, dtype=float)

    # Normalización
    denominadores = np.sqrt(np.sum(matriz**2, axis=0))
    matriz_norm = matriz / denominadores

    # Ponderación
    matriz_pond = matriz_norm * pesos

    # Soluciones ideales
    ideal_pos = np.array([
        np.max(matriz_pond[:, j]) if tipos[j] == 'max' else np.min(matriz_pond[:, j])
        for j in range(len(tipos))
    ])
    ideal_neg = np.array([
        np.min(matriz_pond[:, j]) if tipos[j] == 'max' else np.max(matriz_pond[:, j])
        for j in range(len(tipos))
    ])

    # Distancias
    dist_pos = np.sqrt(np.sum((matriz_pond - ideal_pos)**2, axis=1))
    dist_neg = np.sqrt(np.sum((matriz_pond - ideal_neg)**2, axis=1))

    # Coeficientes de cercanía
    puntuaciones = dist_neg / (dist_pos + dist_neg)
    ranking = np.argsort(-puntuaciones)

    resultados = []
    print("Ranking TOPSIS:")
    for i in ranking:
        nombre = alternativas[i]
        coef = round(puntuaciones[i], 4)
        print(f"{nombre} → Coeficiente: {coef}")
        resultados.append((nombre, coef))

    return render_template("topsis_resultado.html", resultados=resultados)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

