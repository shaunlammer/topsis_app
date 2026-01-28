from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import numpy as np
import sys
import os 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import obtener_historial, CATEGORIAS_CIIU

routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET', 'POST'])
def index():
    historial = obtener_historial()
    num_criterios = None

    if request.method == 'POST':
        
        if 'criterios' in request.form:
            num_criterios = int(request.form['criterios'])
            session["num_criterios"] = num_criterios

        if 'criterio_0' in request.form:
            num_criterios = session.get('num_criterios')

            if num_criterios is None:
                flash("Error: no se encontro el numero de criterios")
                return redirect(url_for('routes.index'))
            
            criterios = []
            for i in range(num_criterios):
                valor = request.form.get(f'criterio_{i}')
                if not valor:
                    flash(f'Falta el nombre de criterio {i+1}')
                    return redirect(url_for('routes.index'))
                criterios.append(valor)

            tipos = [request.form.get(f"tipo_{i}", "max") for i in range(num_criterios)]
            session["criterios"] = criterios
            session["tipos"] = tipos
            return redirect(url_for("routes.ahp"))
        
    return render_template(
        "index.html",
        historial=historial,
        num_criterios=num_criterios,
        categorias_ciiu=CATEGORIAS_CIIU
        )

@routes.route("/matriz", methods=["GET", "POST"])
def ahp():
    criterios = session.get('criterios')
    num_criterios = len(criterios)
    pesos = None

    if request.method == 'POST':
        matriz = []

        for i in range(num_criterios):
            fila = []
            for j in range(num_criterios):
                valor = request.form.get(f'cell_{i}_{j}')
                fila.append(valor)
            matriz.append(fila)

        matriz = np.array(matriz, dtype=float)

        valores, vectores = np.linalg.eig(matriz)
        valores = np.real_if_close(valores)
        vectores = np.real_if_close(vectores)

        indice_max = np.argmax(valores.real)
        vector_eigen = vectores[:, indice_max].real
        pesos = vector_eigen / np.sum(vector_eigen)

        session["matriz_ahp"] = matriz
        session["pesos"] = pesos.tolist()
        return redirect(url_for("routes.alternativas"))

    return render_template(
    "ahp.html",
    criterios=criterios,
    num_criterios=num_criterios,
    pesos=pesos
)

@routes.route("/alternativas", methods=['GET','POST'])
def alternativas():
    criterios = session.get("criterios")
    if criterios is None:
        return redirect(url_for("routes.index"))
    
    num_alt = None
    alternativas = None

    if request.method == "POST" and "num_alternativas" in request.form:
        num_alt = int(request.form["num_alternativas"])
        session["num_alternativas"] = num_alt
        session.pop("alternativas", None)
        return render_template(
            "alternativas.html",
            criterios=criterios,
            num_alt=num_alt,
            alternativas=None
        )
    
    if "alt_0" in request.form:
            num_alt = session.get("num_alternativas")
            
            if num_alt is None:
                flash("Error: no se encontró el número de alternativas")
                return redirect(request.url)
            
            alternativas = []
            for i in range(num_alt):
                nombre = request.form.get(f"alt_{i}")
                if not nombre:
                    flash("Faltan nombres de alternativas")
                    return redirect(request.url)
                alternativas.append(nombre)

            session["alternativas"] = alternativas
            return redirect(url_for("routes.matriz_topsis"))

    return render_template(
        "alternativas.html",
        criterios = criterios,
        num_alt=num_alt,
        alternativas = alternativas
    )

@routes.route("/matriz_topsis", methods=['GET','POST'])
def matriz_topsis():
    criterios = session.get("criterios")
    alternativas = session.get("alternativas")

    if criterios is None or alternativas is None:
        return redirect(url_for("routes.index"))
    
    num_criterios = len(criterios)
    num_alt = len(alternativas)

    if request.method == "POST":
        matriz=[]
        
        for i in range(num_alt):
            fila=[]
            for j in range(num_criterios):
                valor = request.form.get(f"cell_{i}_{j}")
                if valor is None:
                    flash("Faltan valores en la matriz")
                    return redirect(request.url)
                fila.append(float(valor))
            matriz.append(fila)

        session["matriz_topsis"] = matriz
        return redirect(url_for("routes.topsis"))
    
    return render_template(
        "mat_topsis.html",
        criterios=criterios,
        alternativas=alternativas
    )

@routes.route("/topsis")
def topsis():
    criterios = session.get("criterios")
    alternativas = session.get("alternativas")
    matriz = session.get("matriz_topsis")
    pesos = session.get("pesos")
    tipos = session.get("tipos")

    if None in(criterios,alternativas,matriz,pesos,tipos):
        return redirect(url_for("routes.index"))
    
    matriz = np.array(matriz, dtype=float)
    pesos = np.array(pesos, dtype=float)

    denominadores = np.sqrt(np.sum(matriz**2, axis=0))
    matriz_norm = matriz/denominadores

    matriz_pond = matriz_norm * pesos

    ideal_pos = np.array([
        np.max(matriz_pond[:,j]) if tipos[j] == 'max' else np.min(matriz_pond[:,j])
        for j in range(len(tipos))
    ])

    ideal_neg = np.array([
        np.min(matriz_pond[:,j]) if tipos[j] == 'max' else np.max(matriz_pond[:,j])
        for j in range(len(tipos))
    ])

    dist_pos = np.sqrt(np.sum((matriz_pond - ideal_pos)**2, axis=1))
    dist_neg = np.sqrt(np.sum((matriz_pond - ideal_neg)**2, axis=1))

    puntuaciones = dist_neg / (dist_pos + dist_neg)
    ranking = np.argsort(-puntuaciones)

    resultados = [
        (alternativas[i], round(puntuaciones[i],4))
        for i in ranking
    ]

    return render_template(
        "topsis_resultado.html",
        criterios = criterios,
        alternativas=alternativas,
        matriz_norm=matriz_norm,
        matriz_pond=matriz_pond,
        ideal_pos=ideal_pos,
        ideal_neg=ideal_neg,
        resultados=resultados
    )

@routes.route("/guardar_analisis", methods=['POST'])
def guardar_analisis_route():
    from database import guardar_analisis
   
    registro_academico = request.form.get('registro_academico')
    curso = request.form.get('curso')
    descripcion = request.form.get('descripcion')
    

    criterios = session.get("criterios")
    tipos = session.get("tipos")
    matriz_ahp = session.get("matriz_ahp")  
    pesos = session.get("pesos")
    alternativas = session.get("alternativas")
    matriz_evaluacion = session.get("matriz_topsis")
    categoria_ciiu = session.get("categoria_ciiu", "")
    
  
    matriz = np.array(matriz_evaluacion, dtype=float)
    pesos_array = np.array(pesos, dtype=float)
    

    denominadores = np.sqrt(np.sum(matriz**2, axis=0))
    matriz_norm = matriz / denominadores
    
    
    matriz_pond = matriz_norm * pesos_array
    
    
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
    
    resultados = [
        (alternativas[i], round(float(puntuaciones[i]), 4))
        for i in ranking
    ]
    
    
    datos = {
        'nombre_analisis': descripcion,
        'registro_academico': registro_academico,
        'curso': curso,
        'categoria_ciiu': categoria_ciiu,
        'criterios': criterios,
        'tipos_criterios': tipos,
        'matriz_ahp': matriz_ahp if matriz_ahp else [],
        'pesos_ahp': pesos,
        'alternativas': alternativas,
        'matriz_evaluacion': matriz_evaluacion,
        'matriz_normalizada': matriz_norm.tolist(),
        'matriz_ponderada': matriz_pond.tolist(),
        'ideal_positivo': ideal_pos.tolist(),
        'ideal_negativo': ideal_neg.tolist(),
        'ranking_final': resultados
    }
    
    
    resultado = guardar_analisis(datos)
    
    if resultado:
        flash(f'Análisis guardado exitosamente (ID: {resultado})')
        session.clear()
        return redirect(url_for('routes.index'))
    else:
        flash('❌ Error al guardar el análisis')
        return redirect(url_for('routes.topsis'))
    





        
