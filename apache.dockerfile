FROM apache/airflow:2.7.0

USER root
RUN apt-get update && apt-get install -y docker.io
USER airflow


