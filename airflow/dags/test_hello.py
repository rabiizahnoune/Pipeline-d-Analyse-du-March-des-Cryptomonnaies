from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess

default_args = {
    'owner': 'etudiant',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

HADOOP_STREAMING_JAR = "/opt/hadoop-3.2.1/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar"

def check_hdfs_file(path):
    """Vérifie si un fichier HDFS existe."""
    command = ["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-test", "-e", path]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0  # 0 = fichier existe, sinon il manque

def copy_scripts_to_hdfs():
    """Copie les fichiers mapper.py et reducer.py dans HDFS avant d'exécuter MapReduce."""
    subprocess.run(
        ["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-mkdir", "-p", "/user/etudiant/crypto/scripts"],
        check=True
    )
    subprocess.run(
        ["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-put", "-f", 
         "/mnt/hadoop_data/mapreduce/mapper.py", "/user/etudiant/crypto/scripts/mapper.py"],
        check=True
    )
    subprocess.run(
        ["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-put", "-f", 
         "/mnt/hadoop_data/mapreduce/reducer.py", "/user/etudiant/crypto/scripts/reducer.py"],
        check=True
    )

def run_mapreduce_job(**context):
    """Exécute le job MapReduce."""
    execution_date = context['ds']
    year, month, day = execution_date.split('-')

    input_path = f"/user/etudiant/crypto/raw/YYYY={year}/MM={month}/DD={day}/coingecko_raw.json"
    output_path = f"/user/etudiant/crypto/output/YYYY={year}/MM={month}/DD={day}"
    mapper_path = "/user/etudiant/crypto/scripts/mapper.py"
    reducer_path = "/user/etudiant/crypto/scripts/reducer.py"

    # Vérification de l'existence du fichier d'entrée
    print(f"Vérification de l'existence du fichier d'entrée : {input_path}")
    if not check_hdfs_file(input_path):
        print(f"Erreur : Le fichier d'entrée {input_path} n'existe pas dans HDFS.")
        raise ValueError(f"Le fichier HDFS {input_path} n'existe pas.")

    # Supprimer l'ancien répertoire de sortie
    print(f"Suppression de l'ancien répertoire de sortie : {output_path}")
    result_rm = subprocess.run(
        ["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-rm", "-r", output_path],
        capture_output=True, text=True, check=False
    )
    if result_rm.returncode != 0:
        print(f"Avertissement : Échec de la suppression de {output_path}: {result_rm.stderr}")
    else:
        print(f"Ancien répertoire {output_path} supprimé avec succès.")

    # Copier les scripts dans HDFS
    print("Copie des scripts mapper.py et reducer.py dans HDFS.")
    copy_scripts_to_hdfs()

    # Commande Hadoop Streaming
    command = [
        "docker", "exec", "-i", "-u", "root", "namenode", "hadoop", "jar", HADOOP_STREAMING_JAR,
        "-input", input_path,
        "-output", output_path,
        "-mapper", "python3 mapper.py",
        "-reducer", "python3 reducer.py",
        "-file", mapper_path,
        "-file", reducer_path
    ]

    print(f"Exécution de la commande MapReduce : {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    
    # Afficher la sortie et gérer les erreurs
    print(f"Sortie de la commande : {result.stdout}")
    if result.returncode != 0:
        print(f"Erreur lors de l'exécution de MapReduce : {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
    
    print("Job MapReduce exécuté avec succès.")

def fetch_results(**context):
    """Récupère et affiche les résultats depuis HDFS."""
    execution_date = context['ds']
    year, month, day = execution_date.split('-')
    output_path = f"/user/etudiant/crypto/output/YYYY={year}/MM={month}/DD={day}/part-*"

    command = ["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-cat", output_path]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    
    print("Résultats MapReduce :\n", result.stdout)

with DAG(
    'coingecko_mapreduce_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
) as dag:

    run_mapreduce = PythonOperator(
        task_id='run_mapreduce_job',
        python_callable=run_mapreduce_job,
        provide_context=True
    )

    fetch_results_task = PythonOperator(
        task_id='fetch_results',
        python_callable=fetch_results,
        provide_context=True
    )

    run_mapreduce >> fetch_results_task