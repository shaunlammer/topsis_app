#!/bin/bash

# 1. Obtener los últimos cambios de la rama actual
echo "Descargando cambios de Git..."
git pull

# 2. Detener y eliminar el contenedor anterior (si existe) para evitar conflictos
echo "Limpiando contenedores antiguos..."
docker stop topsis-app || true
docker rm topsis-app || true

# 3. Construir la imagen (usamos --no-cache si cambiaste el requirements.txt)
echo "Construyendo la imagen..."
docker build -t topsis-image .

# 4. Levantar el nuevo contenedor en el puerto 7000 (que es el que definimos antes)
echo "Levantando el contenedor en el puerto 7000..."
docker run -d \
  -p 7000:7000 \
  --add-host=host.docker.internal:host-gateway \
  --name topsis-app \
  --restart unless-stopped \
  topsis-image

echo "¡Despliegue finalizado con éxito!"