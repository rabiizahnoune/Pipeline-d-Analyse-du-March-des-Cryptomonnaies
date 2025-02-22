# Utiliser une image Python légère
FROM python:3.8-slim  

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers nécessaires
COPY . .

RUN pip install --upgrade pip
RUN  pip install pandas
# Installer les dépendances si un fichier requirements.txt existe

# S'assurer que le script peut s'exécuter
RUN chmod +x mapper.py

# Lancer le script automatiquement (peut être modifié)
CMD ["bash"]
