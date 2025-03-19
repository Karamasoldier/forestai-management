FROM python:3.9-slim

WORKDIR /app

# Copier les fichiers de requirements avant le reste pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p logs data/cache

# Exposer le port API
EXPOSE 8000

# Commande par défaut
CMD ["python", "api_server_fix.py", "--host", "0.0.0.0", "--port", "8000"]