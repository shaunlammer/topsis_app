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

EXPOSE 5000

# Asegúrate de que en app.py el host sea '0.0.0.0' y el puerto 7000
CMD ["python", "app.py"]