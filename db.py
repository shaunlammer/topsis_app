import mysql.connector
from flask import current_app, g

def get_db():
    """
    Obtiene una conexión a la base de datos y la guarda en 'g'
    para reutilizarla durante la petición.
    """
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
        )
    return g.db

def close_db(e=None):
    """
    Cierra la conexión almacenada en 'g' si existe.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()
