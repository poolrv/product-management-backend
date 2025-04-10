FROM python:3.9-slim

WORKDIR /app

# Instalar curl para el healthcheck
RUN apt-get update && apt-get install -y curl && apt-get clean

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Crear un script de inicio para manejar errores de conexión
RUN echo '#!/bin/bash\n\
# Esperar intentando conectarse a la base de datos\n\
echo "Esperando a que la base de datos esté disponible..."\n\
sleep 5\n\
# Iniciar gunicorn\n\
gunicorn --bind 0.0.0.0:5000 app:app\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 5000

# Health check más tolerante
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Usar el script de inicio en lugar de gunicorn directamente
CMD ["/app/start.sh"]