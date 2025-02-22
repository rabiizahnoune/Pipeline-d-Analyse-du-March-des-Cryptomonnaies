# from airflow import DAG
# from airflow.operators.bash import BashOperator
# from datetime import datetime

# # -------------------- Définition du DAG --------------------
# default_args = {
#     'owner': 'airflow',
#     'start_date': datetime(2024, 1, 1),
# }

# with DAG(
#     'test_docker_exec_hadoop',
#     default_args=default_args,
#     schedule_interval='@once',  # Exécuter une seule fois pour le test
#     catchup=False
# ) as dag:

#     create_test_file = BashOperator(
#         task_id='create_test_file_in_container',
#         bash_command='docker exec -i airflow-webserver bash -c "touch /mnt/hadoop_data/mon_fichier.txt"'

#     )

#     check_test_file = BashOperator(
#         task_id='check_test_file_in_container',
#         bash_command='docker exec -i hadoop-datanode bash -c "cat /mnt/hadoop_data/mon_fichier.txt"'
#     )

#     create_test_file >> check_test_file  # Définir l'ordre d'exécution


from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import json
import subprocess   
import os
default_args = {
    'owner': 'etudiant',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def fetch_coingecko_data(**context):
    """Récupère les données depuis l'API CoinGecko et les stocke localement."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    # Sauvegarde locale du fichier
    local_file = "/tmp/coingecko_raw.json"
    with open(local_file, 'w') as f:
        json.dump(data, f)
    
    # Pousser le chemin du fichier dans XCom
    context['ti'].xcom_push(key='local_file', value=local_file)

# def store_raw_data_in_hdfs(**context):
#     """Copie les données dans le conteneur Hadoop et les stocke dans HDFS."""
#     local_file = context['ti'].xcom_pull(key='local_file')
#     if not os.path.exists(local_file):
#         raise FileNotFoundError(f"Le fichier local n'a pas été trouvé: {local_file}")
    

#     # Construire le chemin HDFS basé sur la date d'exécution
#     execution_date = context['ds']  # ex: '2025-01-01'
#     year, month, day = execution_date.split('-')
#     hdfs_dir = f"/user/etudiant/crypto/raw/YYYY={year}/MM={month}/DD={day}"
#     hdfs_file_path = f"{hdfs_dir}/coingecko_raw.json"
# #     pathh = f"etudiant/crypto/raw/YYYY={year}/MM={month}"
# #     subprocess.run([
# #     "docker", "exec", "-u", "root", "-i", "hadoop-namenode", "bash", "-c",
# #     f"hdfs dfs -rm -r {pathh} || true"  # Utilisez || true pour éviter les erreurs si le répertoire n'existe pas
# # ])


#     # Copier le fichier dans le conteneur Hadoop NameNode
# #     subprocess.run([
# #     "docker", "exec", "-u", "root", "-i", "hadoop-namenode", "bash", "-c",
# #     f"hdfs dfs -chmod 777 {hdfs_dir} && hdfs dfs -mkdir -p {hdfs_dir} && hdfs dfs -put -f {local_file} {hdfs_file_path}"
# # ])
#    # Copier le fichier dans le conteneur Hadoop NameNode
#     # Copier le fichier dans le conteneur Hadoop NameNode
#     subprocess.run(["docker", "cp", local_file, "hadoop-namenode:/mnt/hadoop_data/coingecko_raw.json"])
#     x = r"/mnt/hadoop_data/coingecko_raw.json"

#     # Exécuter les commandes HDFS dans le conteneur NameNode
#     subprocess.run([
#         "docker", "exec", "-i", "hadoop-namenode", "bash", "-c",
#         f"hdfs dfs -mkdir -p {hdfs_dir}"
#     ])

#     # Vérifier les permissions du dossier HDFS
#     subprocess.run([
#       "docker", "exec", "-i", "hadoop-namenode", "bash", "-c",
#       f"hdfs dfs -chmod 777 {hdfs_dir}"
# ])
#     subprocess.run([
#     "docker", "exec", "-i", "hadoop-namenode", "bash", "-c",
#     f"hdfs dfs -put -f /mnt/hadoop_data/coingecko_raw.json {hdfs_file_path}"
# ])
def store_raw_data_in_hdfs(**context):
    import hdfs3

    local_file = context['ti'].xcom_pull(key='local_file')
    execution_date = context['ds']
    year, month, day = execution_date.split('-')

    hdfs_client = hdfs3.HDFileSystem(host='hadoop-namenode', port=8020)
    hdfs_dir = f"/user/etudiant/crypto/raw/YYYY={year}/MM={month}/DD={day}"
    hdfs_file_path = f"{hdfs_dir}/coingecko_raw.json"

    # Créer le répertoire s'il n'existe pas
    if not hdfs_client.exists(hdfs_dir):
        hdfs_client.mkdir(hdfs_dir)

    # Charger le fichier local vers HDFS
    with open(local_file, 'rb') as f:
        hdfs_client.put(f, hdfs_file_path)


with DAG(
    'coingecko_ingestion_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
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
