import traceback
import logging
from flask import Flask, render_template, request
from routes.main import routes

app = Flask(__name__)
app.secret_key = "ahp_secret"

# Logging a stdout para que aparezca en docker logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

app.register_blueprint(routes)

@app.errorhandler(404)
def not_found(error):
    app.logger.warning(f'404 Not Found: {request.path}')
    return render_template('error.html',
                           mensaje="Página no encontrada. La ruta que buscas no existe."), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'500 Internal Server Error:\n{traceback.format_exc()}')
    return render_template('error.html',
                           mensaje="Error interno del servidor. Por favor, intenta de nuevo más tarde."), 500

@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error(f'Excepción no manejada: {type(error).__name__}: {error}\n{traceback.format_exc()}')
    return render_template('error.html',
                           mensaje=f"Error inesperado: {type(error).__name__} — {error}"), 500

if __name__ == "__main__":
 app.run(debug=True, host='0.0.0.0', port=5000)
