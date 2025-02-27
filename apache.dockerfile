# Utiliser une image officielle Airflow comme base
FROM apache/airflow:2.7.1

# Passer en root pour installer des paquets système
USER root

# Installer les outils de compilation et les dépendances nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libssl-dev \
    && apt-get clean

# Revenir à l'utilisateur airflow pour les installations pip
USER airflow

# Installer les dépendances Python
RUN pip install --no-cache-dir \
    yfinance \
    ta \
    pandas \
    happybase