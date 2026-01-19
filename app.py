from flask import Flask
from routes.main import routes

app = Flask(__name__)
app.secret_key = "ahp_secret"

app.register_blueprint(routes)

print(app.url_map)   # ← AQUÍ

if __name__ == "__main__":
    app.run(debug=True, port=5000)
