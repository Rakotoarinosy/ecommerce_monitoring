# Utilisation de l'image Python officielle
FROM python:3.10-slim

# Définition du répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt ./

# Installer les dépendances (avant le code : une modification de app/ ne réinstalle rien)
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Exposer le port de l'API
EXPOSE 8011

# Lancer l'application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8011", "--reload"]
