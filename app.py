from flask import Flask, render_template
from routes.main import routes

app = Flask(__name__)
app.secret_key = "ahp_secret"  

app.register_blueprint(routes)

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         mensaje="Página no encontrada. La ruta que buscas no existe."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         mensaje="Error interno del servidor. Por favor, intenta de nuevo más tarde."), 500

@app.errorhandler(Exception)
def handle_exception(error):
    # Log del error para debugging
    app.logger.error(f'Error no manejado: {error}')
    return render_template('error.html', 
                         mensaje="Ha ocurrido un error inesperado. El equipo técnico ha sido notificado."), 500

if __name__ == "__main__":
 app.run(debug=True, port=5000)
