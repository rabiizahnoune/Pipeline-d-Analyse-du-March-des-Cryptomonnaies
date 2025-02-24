from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import requests
import json
import subprocess

default_args = {
    'owner': 'etudiant',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def fetch_coingecko_data(**context):
    """Récupère les données depuis l'API CoinGecko."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': '100',
        'page': '1',
        'sparkline': 'false'
    }
    response = requests.get(url, params=params)
    data = response.json()
    # On push les données dans XCom pour la prochaine tâche
    context['ti'].xcom_push(key='raw_data', value=data)

def store_raw_data_in_hdfs(**context):
    """Stocke les données brutes dans HDFS avec partition par date."""
    data = context['ti'].xcom_pull(key='raw_data')
    json_data = json.dumps(data)

    # Chemin local temporaire
    local_file = '/mnt/hadoop_data/coingecko_raw.json'
    with open(local_file, 'w') as f:
        f.write(json_data)

    # On construit le chemin HDFS à partir de la date d'exécution
    execution_date = context['ds']  # ex: '2025-01-01'
    year, month, day = execution_date.split('-')
    hdfs_dir = f"/user/etudiant/crypto/raw/YYYY={year}/MM={month}/DD={day}"
    hdfs_file_path = f"{hdfs_dir}/coingecko_raw.json"

    # Création du répertoire et mise en HDFS
    subprocess.run(["docker","exec","-i","-u","root","namenode","hdfs", "dfs", "-mkdir", "-p", hdfs_dir])
    subprocess.run(["docker","exec","-i","-u","root","namenode","hdfs", "dfs", "-put", "-f", local_file, hdfs_file_path])

with DAG(
    'coingecko_ingestion_dag',
    default_args=default_args,
    schedule_interval='@daily'
) as dag:

    fetch_data = PythonOperator(
        task_id='fetch_data',
        python_callable=fetch_coingecko_data,
        provide_context=True
    )

    store_raw_data = PythonOperator(
        task_id='store_raw_data_in_hdfs',
        python_callable=store_raw_data_in_hdfs,
        provide_context=True
    )

    fetch_data >> store_raw_data

