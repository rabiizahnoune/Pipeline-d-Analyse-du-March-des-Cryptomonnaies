from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import json
import subprocess

default_args = {
    'owner': 'etudiant',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def fetch_crypto_data(**context):
    """Récupère les données horaires des 3 cryptos depuis yfinance."""
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    all_data = []
    
    for symbol in symbols:
        try:
            crypto = yf.Ticker(symbol)
            df = crypto.history(
                start=start_time,
                end=end_time,
                interval='1h'
            )
            
            if df.empty:
                print(f"Aucune donnée pour {symbol}")
                continue
                
            df = df.reset_index()
            df = df.rename(columns={
                'Datetime': 'datetime',
                'Open': 'open_price',
                'High': 'high_price',
                'Low': 'low_price',
                'Close': 'close_price',
                'Volume': 'volume'
            })
            df['coin'] = symbol.replace('-USD', '')
            
            columns_to_keep = ['datetime', 'open_price', 'high_price', 'low_price', 
                             'close_price', 'volume', 'coin']
            df = df[columns_to_keep]
            
            # Conversion des timestamps en chaînes ISO pour JSON
            df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            all_data.append(df)
            
        except Exception as e:
            print(f"Erreur lors de la récupération de {symbol}: {e}")
            continue
    
    if not all_data:
        raise ValueError("Aucune donnée récupérée depuis yfinance")
        
    # Combinaison des données
    final_df = pd.concat(all_data)
    
    # Conversion en liste de dictionnaires
    json_data = final_df.to_dict(orient='records')
    
    # Aperçu des données
    print(json.dumps(json_data[:5], indent=4))
    
    # Push dans XCom
    context['ti'].xcom_push(key='raw_data', value=json_data)

def store_raw_data_in_hdfs(**context):
    """Stocke les données brutes dans HDFS avec partition par date."""
    data = context['ti'].xcom_pull(key='raw_data')
    
    # Écriture dans le fichier local
    local_file = '/mnt/hadoop_data/yfinance_raw.json'
    with open(local_file, 'w') as f:
        json.dump(data, f, indent=4)
    
    # Chemin HDFS basé sur la date d'exécution
    execution_date = context['ds']
    year, month, day = execution_date.split('-')
    hdfs_dir = f"/user/etudiant/crypto/raw/YYYY={year}/MM={month}/DD={day}"
    hdfs_file_path = f"{hdfs_dir}/yfinance_raw.json"

    # Création du répertoire et stockage dans HDFS
    subprocess.run(["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-mkdir", "-p", hdfs_dir])
    subprocess.run(["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-put", "-f", local_file, hdfs_file_path])

with DAG(
    'yfinance_ingestion_dag',  # Nom corrigé
    default_args=default_args,
    schedule_interval='@daily'
) as dag:

    fetch_data = PythonOperator(
        task_id='fetch_data',
        python_callable=fetch_crypto_data,
        provide_context=True
    )

    store_raw_data = PythonOperator(
        task_id='store_raw_data_in_hdfs',
        python_callable=store_raw_data_in_hdfs,
        provide_context=True
    )

    fetch_data >> store_raw_data