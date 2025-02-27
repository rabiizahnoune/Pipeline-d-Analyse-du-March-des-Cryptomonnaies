# Utiliser l'image de base du namenode
FROM bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
USER root

# Remplacer les dépôts obsolètes par archive.debian.org
RUN echo "deb http://archive.debian.org/debian stretch main" > /etc/apt/sources.list && \
    echo "deb http://archive.debian.org/debian-security stretch/updates main" >> /etc/apt/sources.list

# Installer Python 3
RUN apt-get update && apt-get install -y python3 && ln -s /usr/bin/python3 /usr/bin/python

# Vérifier l'installation
RUN python --version