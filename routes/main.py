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
        
        if 'criterios' in request.form and 'categorias_ciiu' in request.form:
            num_criterios = int(request.form['criterios'])
            categoria_ciiu = request.form['categoria_ciiu']
            
            session["num_criterios"] = num_criterios
            session["categoria_ciiu"] = categoria_ciiu            
            
            return redirect(url_for('routes.index'))

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
            session.pop('num_criterios', None)
            return redirect(url_for("routes.ahp"))
        
    return render_template(
        "index.html",
        historial=historial,
        num_criterios=num_criterios,
        categorias_ciiu=CATEGORIAS_CIIU
        )

@routes.route("/matriz", methods=["GET", "POST"])
def ahp():
    try:
        criterios = session.get('criterios')
        if criterios is None:
            flash("No se encontraron criterios.", 'warning')
            return redirect(url_for("routes.index"))
        
        num_criterios = len(criterios)
        pesos = None

        if request.method == 'POST':
            matriz = []

            for i in range(num_criterios):
                fila = []
                for j in range(num_criterios):
                    valor = request.form.get(f'cell_{i}_{j}')
                    
                    try:
                        # Convertir fracción a decimal si tiene /
                        if '/' in valor:
                            numerador, denominador = valor.split('/')
                            valor_float = float(numerador) / float(denominador)
                        else:
                            valor_float = float(valor)
                        
                        # Validar rango
                        if valor_float < 0.11 or valor_float > 9:
                            flash(f"El valor en fila {i+1}, columna {j+1} debe estar entre 0.11 y 9", 'warning')
                            return redirect(request.url)
                        
                        fila.append(valor_float)
                        
                    except (ValueError, TypeError, ZeroDivisionError):  # ← Cerrar el try interno
                        flash(f"Valor inválido en fila {i+1}, columna {j+1}", 'error')
                        return redirect(request.url)
                
                matriz.append(fila)

            matriz_array = np.array(matriz, dtype=float)

            valores, vectores = np.linalg.eig(matriz_array)
            valores = np.real_if_close(valores)
            vectores = np.real_if_close(vectores)

            indice_max = np.argmax(valores.real)
            vector_eigen = vectores[:, indice_max].real
            pesos = vector_eigen / np.sum(vector_eigen)

            session["matriz_ahp"] = matriz
            session["pesos"] = pesos.tolist()
            
            flash('✅ Pesos calculados exitosamente', 'success')

        return render_template(
            "ahp.html",
            criterios=criterios,
            num_criterios=num_criterios,
            pesos=pesos
        )
    
    except Exception as e:  # ← Cerrar el try externo
        print(f'Error en AHP: {e}')
        flash("❌ Error al calcular los pesos AHP. Por favor, verifica los valores ingresados.", 'error')
        return redirect(url_for("routes.index"))

@routes.route("/alternativas", methods=['GET','POST'])
def alternativas():
    criterios = session.get("criterios")
    if criterios is None:
        flash("⚠️ No se encontraron criterios.", 'warning')
        return redirect(url_for("routes.index"))
    
    num_alt = session.get("num_alternativas")
    alternativas = session.get("alternativas")

    if request.method == "POST":
        # Paso 1: Guardar número de alternativas
        if "num_alternativas" in request.form:
            num_alt = int(request.form["num_alternativas"])
            session["num_alternativas"] = num_alt
            session.pop("alternativas", None)
            return redirect(url_for("routes.alternativas"))  # ← Redirigir
        
        # Paso 2: Guardar nombres de alternativas
        if "alt_0" in request.form:
            num_alt = session.get("num_alternativas")
            
            if num_alt is None:
                flash("⚠️ Error: no se encontró el número de alternativas", 'warning')
                return redirect(url_for("routes.alternativas"))
            
            alternativas = []
            for i in range(num_alt):
                nombre = request.form.get(f"alt_{i}")
                if not nombre:
                    flash("⚠️ Faltan nombres de alternativas", 'warning')
                    return redirect(url_for("routes.alternativas"))
                alternativas.append(nombre)

            session["alternativas"] = alternativas
            session.pop("num_alternativas", None)
            return redirect(url_for("routes.matriz_topsis"))

    return render_template(
        "alternativas.html",
        criterios=criterios,
        num_alt=num_alt,
        alternativas=alternativas
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

    session["matriz_normalizada"] = matriz_norm.tolist()
    session["matriz_ponderada"] = matriz_pond.tolist()
    session["ideal_positivo"] = ideal_pos.tolist()
    session["ideal_negativo"] = ideal_neg.tolist()
    session["ranking_final"] = resultados

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
    matriz_ahp = session.get("matriz_ahp", [])
    pesos = session.get("pesos")
    alternativas = session.get("alternativas")
    matriz_evaluacion = session.get("matriz_topsis")
    categoria_ciiu = session.get("categoria_ciiu", "")
    
    matriz_normalizada = session.get("matriz_normalizada")
    matriz_ponderada = session.get("matriz_ponderada")
    ideal_positivo = session.get("ideal_positivo")
    ideal_negativo = session.get("ideal_negativo")
    ranking_final = session.get("ranking_final")
    

    datos = {
        'nombre_analisis': descripcion,
        'registro_academico': registro_academico,
        'curso': curso,
        'categoria_ciiu': categoria_ciiu,
        'criterios': criterios,
        'tipos_criterios': tipos,
        'matriz_ahp': matriz_ahp,
        'pesos_ahp': pesos,
        'alternativas': alternativas,
        'matriz_evaluacion': matriz_evaluacion,
        'matriz_normalizada': matriz_normalizada,
        'matriz_ponderada': matriz_ponderada,
        'ideal_positivo': ideal_positivo,
        'ideal_negativo': ideal_negativo,
        'ranking_final': ranking_final
    }
   
    resultado = guardar_analisis(datos)
    
    if resultado:
        flash(f'Análisis guardado exitosamente (ID: {resultado})')
        session.clear()
        return redirect(url_for('routes.index'))
    else:
        flash('Error al guardar el análisis')
        return redirect(url_for('routes.topsis'))

@routes.route("/ver_analisis/<int:id>")
def ver_analisis(id):
    from database import obtener_analisis_por_id
    
    analisis = obtener_analisis_por_id(id)
    
    if not analisis:
        flash("Análisis no encontrado")
        return redirect(url_for('routes.index'))
    
    return render_template(
        "ver_analisis.html",
        analisis=analisis
    )

@routes.route("/eliminar_analisis/<int:id>")
def eliminar_analisis(id):
    from database import eliminar_analisis as eliminar_db
    
    resultado = eliminar_db(id)
    
    if resultado:
        flash("Análisis eliminado correctamente")
    else:
        flash("Error al eliminar el análisis")
    
    return redirect(url_for('routes.index'))





        
