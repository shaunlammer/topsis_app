import pymysql
import json
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Por defecto XAMPP no tiene contraseña
    'database': 'topsis_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Crear conexión a la base de datos"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def test_connection():
    """Probar la conexión a la base de datos"""
    conn = get_db_connection()
    if conn:
        print("Conexión exitosa a la base de datos")
        conn.close()
        return True
    else:
        print("Error al conectar a la base de datos")
        return False

# Funciones CRUD

def guardar_analisis(datos):
    """
    Guardar un nuevo análisis TOPSIS en la base de datos
    
    datos = {
        'nombre_analisis': str,
        'registro_academico': str,
        'curso': str,
        'categoria_ciiu': str,
        'criterios': list,
        'tipos_criterios': list,
        'matriz_ahp': list,
        'pesos_ahp': list,
        'alternativas': list,
        'matriz_evaluacion': list,
        'matriz_normalizada': list,
        'matriz_ponderada': list,
        'ideal_positivo': list,
        'ideal_negativo': list,
        'ranking_final': list
    }
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO analisis_topsis 
            (nombre_analisis, registro_academico, curso, fecha_creacion, categoria_ciiu,
             criterios, tipos_criterios, matriz_ahp, pesos_ahp,
             alternativas, matriz_evaluacion, matriz_normalizada, matriz_ponderada,
             ideal_positivo, ideal_negativo, ranking_final)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                datos['nombre_analisis'],
                datos['registro_academico'],
                datos['curso'],
                datetime.now(),
                datos.get('categoria_ciiu', ''),
                json.dumps(datos['criterios']),
                json.dumps(datos['tipos_criterios']),
                json.dumps(datos['matriz_ahp']),
                json.dumps(datos['pesos_ahp']),
                json.dumps(datos['alternativas']),
                json.dumps(datos['matriz_evaluacion']),
                json.dumps(datos['matriz_normalizada']),
                json.dumps(datos['matriz_ponderada']),
                json.dumps(datos['ideal_positivo']),
                json.dumps(datos['ideal_negativo']),
                json.dumps(datos['ranking_final'])
            ))
            
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False
    finally:
        conn.close()

def obtener_historial():
    """Obtener todos los análisis guardados"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT id, nombre_analisis, registro_academico, curso, 
                   fecha_creacion, categoria_ciiu,
                   ranking_final
            FROM analisis_topsis 
            ORDER BY fecha_creacion DESC
            """
            cursor.execute(sql)
            resultados = cursor.fetchall()
            
            # Parsear JSON de ranking_final
            for row in resultados:
                row['ranking_final'] = json.loads(row['ranking_final'])
                row['fecha_creacion'] = row['fecha_creacion'].strftime('%d-%m-%Y %H:%M')
            
            return resultados
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return []
    finally:
        conn.close()

def obtener_analisis_por_id(analisis_id):
    """Obtener un análisis completo por su ID"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM analisis_topsis WHERE id = %s"
            cursor.execute(sql, (analisis_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                # Parsear todos los campos JSON
                campos_json = [
                    'criterios', 'tipos_criterios', 'matriz_ahp', 'pesos_ahp',
                    'alternativas', 'matriz_evaluacion', 'matriz_normalizada',
                    'matriz_ponderada', 'ideal_positivo', 'ideal_negativo', 'ranking_final'
                ]
                
                for campo in campos_json:
                    if resultado[campo]:
                        resultado[campo] = json.loads(resultado[campo])
                
                return resultado
            return None
    except Exception as e:
        print(f"Error al obtener análisis: {e}")
        return None
    finally:
        conn.close()

def eliminar_analisis(analisis_id):
    """Eliminar un análisis por su ID"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM analisis_topsis WHERE id = %s"
            cursor.execute(sql, (analisis_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error al eliminar: {e}")
        return False
    finally:
        conn.close()

# Categorías CIIU Guatemala
CATEGORIAS_CIIU = {
    "": "-- Selecciona una categoría --",
    "A": "Agricultura, ganadería, silvicultura y pesca",
    "C": "Industrias manufactureras",
    "D": "Suministro de electricidad, gas, vapor",
    "E": "Suministro de agua; evacuación de aguas residuales",
    "F": "Construcción",
    "G": "Comercio al por mayor y al por menor",
    "H": "Transporte y almacenamiento",
    "I": "Actividades de alojamiento y de servicio de comidas",
    "J": "Información y comunicaciones",
    "K": "Actividades financieras y de seguros",
    "L": "Actividades inmobiliarias",
    "M": "Actividades profesionales, científicas y técnicas",
    "N": "Actividades de servicios administrativos",
    "O": "Administración pública y defensa",
    "P": "Enseñanza",
    "Q": "Actividades de atención de la salud humana",
    "R": "Actividades artísticas, de entretenimiento",
    "S": "Otras actividades de servicios",
}

# Lista de cursos comunes
CURSOS = [
    "Investigación de Operaciones 1",
    "Investigación de Operaciones 2",
    "Ingenieria de Plantas",
    "Otro"
]