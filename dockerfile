FROM python:3.11-slim

WORKDIR /app

# Instalamos dependencias mínimas del sistema por si acaso
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instalamos dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Variables de entorno para la conexión a la base de datos.
# Sobreescribe estos valores al correr el contenedor:
#   docker run --env-file .env ...
#   o bien con -e DB_HOST=... -e DB_USER=... etc.
ENV DB_HOST=localhost \
    DB_USER=root \
    DB_PASSWORD="" \
    DB_NAME=topsis_db \
    DB_PORT=3306

EXPOSE 5000

# Asegúrate de que en app.py el host sea '0.0.0.0' y el puerto 7000
CMD ["python", "app.py"]