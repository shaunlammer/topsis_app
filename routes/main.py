from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import numpy as np
import sys
import os 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import obtener_historial, CATEGORIAS_CIIU, CURSOS

routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET', 'POST'])
def index():
    historial = obtener_historial()
    
    if request.method == 'GET':
        if not session.get('iniciando'):
            session.pop('num_criterios', None)
        else:
            session.pop('iniciando', None) 

    num_criterios = session.get('num_criterios')

    if request.method == 'POST':

        # Primera fase: capturar TODOS los datos iniciales
        if 'criterios' in request.form and 'categoria_ciiu' in request.form:
            session['num_criterios'] = int(request.form['criterios'])
            
            # Validar rango server-side
            if session['num_criterios'] < 2 or session['num_criterios'] > 10:
                flash("El número de criterios debe estar entre 2 y 10", "error")
                session.pop('num_criterios', None)
                return redirect(url_for('routes.index'))
            
            session['categoria_ciiu'] = request.form['categoria_ciiu']
            session['registro_academico'] = request.form.get('registro_academico', '')
            session['curso'] = request.form.get('curso', '')
            session['iniciando'] = True

            return redirect(url_for('routes.index'))
            
        # Segunda fase: nombres de criterios
        if 'criterio_0' in request.form:
            num_criterios = session.get('num_criterios')

            if not num_criterios:
                flash("No se encontró el número de criterios", "error")
                return redirect(url_for('routes.index'))

            criterios = []
            tipos = []

            for i in range(num_criterios):
                nombre = request.form.get(f'criterio_{i}')
                tipo = request.form.get(f'tipo_{i}', 'max')

                if not nombre:
                    flash(f"Falta el nombre del criterio {i+1}", "error")
                    return redirect(url_for('routes.index'))

                criterios.append(nombre.strip()[:100])
                tipos.append(tipo)

            session['criterios'] = criterios
            session['tipos'] = tipos
            session.pop('num_criterios', None)

            return redirect(url_for('routes.ahp'))

    return render_template(
        'index.html',
        historial=historial,
        num_criterios=num_criterios,
        categorias_ciiu=CATEGORIAS_CIIU,
        cursos=CURSOS,
        active_page='inicio'
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
                        if '/' in valor:
                            numerador, denominador = valor.split('/')
                            valor_float = float(numerador) / float(denominador)
                        else:
                            valor_float = float(valor)
                        
                        if valor_float < 0.11 or valor_float > 9:
                            flash(f"El valor en fila {i+1}, columna {j+1} debe estar entre 0.11 y 9", 'warning')
                            return redirect(request.url)
                        
                        fila.append(valor_float)
                        
                    except (ValueError, TypeError, ZeroDivisionError):
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
            
            flash('Pesos calculados exitosamente', 'success')

        return render_template(
            "ahp.html",
            criterios=criterios,
            num_criterios=num_criterios,
            pesos=pesos,
            active_page='nuevo'
        )
    
    except Exception as e:  
        print(f'Error en AHP: {e}')
        flash("Error al calcular los pesos AHP. Por favor, verifica los valores ingresados.", 'error')
        return redirect(url_for("routes.index"))

@routes.route("/alternativas", methods=['GET','POST'])
def alternativas():
    criterios = session.get("criterios")
    if criterios is None:
        flash("No se encontraron criterios.", 'warning')
        return redirect(url_for("routes.index"))
    
    num_alt = session.get("num_alternativas")
    alternativas = session.get("alternativas")

    if request.method == "POST":
        if "num_alternativas" in request.form:
            try:
                num_alt = int(request.form["num_alternativas"])
            except (ValueError, TypeError):
                flash("El número de alternativas debe ser un entero", "error")
                return redirect(url_for("routes.alternativas"))
            
            if num_alt < 2 or num_alt > 20:
                flash("El número de alternativas debe estar entre 2 y 20", "error")
                return redirect(url_for("routes.alternativas"))
            
            session["num_alternativas"] = num_alt
            session.pop("alternativas", None)
            return redirect(url_for("routes.alternativas")) 
        
        if "alt_0" in request.form:
            num_alt = session.get("num_alternativas")
            
            if num_alt is None:
                flash("Error: no se encontró el número de alternativas", 'warning')
                return redirect(url_for("routes.alternativas"))
            
            alternativas_list = []
            for i in range(num_alt):
                nombre = request.form.get(f"alt_{i}")
                if not nombre or not nombre.strip():
                    flash("Faltan nombres de alternativas", 'warning')
                    return redirect(url_for("routes.alternativas"))
                nombre = nombre.strip()[:100]  # Limitar longitud
                alternativas_list.append(nombre)

            session["alternativas"] = alternativas_list
            session.pop("num_alternativas", None)
            return redirect(url_for("routes.matriz_topsis"))

    return render_template(
        "alternativas.html",
        criterios=criterios,
        num_alt=num_alt,
        alternativas=alternativas,
        active_page='nuevo'
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
        matriz = []
        
        for i in range(num_alt):
            fila = []
            for j in range(num_criterios):
                valor = request.form.get(f"cell_{i}_{j}")
                if valor is None or valor.strip() == '':
                    flash(f"Falta el valor en fila {i+1}, columna {j+1}", "error")
                    return redirect(request.url)
                
                valor = valor.strip()
                
                # Validar que sea un entero (no decimales, no letras, no caracteres raros)
                try:
                    numero = int(valor)
                except (ValueError, TypeError):
                    flash(f"El valor en fila {i+1}, columna {j+1} debe ser un número entero (ingresaste: '{valor}')", "error")
                    return redirect(request.url)
                
                # Validar que el string original no tenga decimales (prevenir "50.0" -> 50)
                if '.' in valor or ',' in valor:
                    flash(f"El valor en fila {i+1}, columna {j+1} no puede tener decimales", "error")
                    return redirect(request.url)
                
                # Validar rango 0-100
                if numero < 0 or numero > 100:
                    flash(f"El valor en fila {i+1}, columna {j+1} debe estar entre 0 y 100 (ingresaste: {numero})", "error")
                    return redirect(request.url)
                
                fila.append(float(numero))
            matriz.append(fila)

        session["matriz_topsis"] = matriz
        return redirect(url_for("routes.topsis"))
    
    return render_template(
        "mat_topsis.html",
        criterios=criterios,
        alternativas=alternativas,
        active_page='nuevo'
    )

@routes.route("/topsis")
def topsis():
    criterios = session.get("criterios")
    alternativas = session.get("alternativas")
    matriz = session.get("matriz_topsis")
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

    resultados = [
        (alternativas[i], round(puntuaciones[i], 4))
        for i in ranking
    ]

    session["matriz_normalizada"] = matriz_norm.tolist()
    session["matriz_ponderada"] = matriz_pond.tolist()
    session["ideal_positivo"] = ideal_pos.tolist()
    session["ideal_negativo"] = ideal_neg.tolist()
    session["ranking_final"] = resultados

    # Datos del inicio del flujo
    registro_academico = session.get("registro_academico", "")
    curso = session.get("curso", "")
    categoria_ciiu = session.get("categoria_ciiu", "")

    return render_template(
        "topsis_resultado.html",
        criterios=criterios,
        alternativas=alternativas,
        matriz_norm=matriz_norm,
        matriz_pond=matriz_pond,
        ideal_pos=ideal_pos,
        ideal_neg=ideal_neg,
        resultados=resultados,
        registro_academico=registro_academico,
        curso=curso,
        categoria_ciiu=categoria_ciiu,
        active_page='nuevo'
    )

@routes.route("/guardar_analisis", methods=['POST'])
def guardar_analisis_route():
    from database import guardar_analisis
    
    descripcion = request.form.get('descripcion')
    
    # Datos capturados al INICIO del flujo (desde la sesión)
    registro_academico = session.get("registro_academico", "")
    curso = session.get("curso", "")
    categoria_ciiu = session.get("categoria_ciiu", "")
    
    criterios = session.get("criterios")
    tipos = session.get("tipos")
    matriz_ahp = session.get("matriz_ahp", [])
    pesos = session.get("pesos")
    alternativas = session.get("alternativas")
    matriz_evaluacion = session.get("matriz_topsis")
    
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
        flash(f'Análisis guardado exitosamente (ID: {resultado})', 'success')
        session.clear()
        return redirect(url_for('routes.index'))
    else:
        flash('Error al guardar el análisis', 'error')
        return redirect(url_for('routes.topsis'))

@routes.route("/ver_analisis/<int:id>")
def ver_analisis(id):
    from database import obtener_analisis_por_id
    
    analisis = obtener_analisis_por_id(id)
    
    if not analisis:
        flash("Análisis no encontrado", "error")
        return redirect(url_for('routes.index'))
    
    return render_template(
        "ver_analisis.html",
        analisis=analisis,
        active_page='inicio'
    )

@routes.route("/eliminar_analisis/<int:id>")
def eliminar_analisis(id):
    from database import eliminar_analisis as eliminar_db
    
    resultado = eliminar_db(id)
    
    if resultado:
        flash("Análisis eliminado correctamente", "success")
    else:
        flash("Error al eliminar el análisis", "error")
    
    return redirect(url_for('routes.index'))





        
