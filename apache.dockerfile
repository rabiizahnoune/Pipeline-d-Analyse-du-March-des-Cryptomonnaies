FROM apache/airflow:2.7.0

USER root
RUN apt-get update && apt-get install -y docker.io
USER airflow
RUN pip install --upgrade pip
# Installer les dépendances si un fichier requirements.txt existe
RUN pip install yfinance ta pandas


