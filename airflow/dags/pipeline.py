from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import json
import subprocess
import happybase

default_args = {
    'owner': 'etudiant',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 0,
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
    data = context['ti'].xcom_pull(key='raw_data')
    local_file = '/mnt/hadoop_data/yfinance_raw.json'
    with open(local_file, 'w') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')  # Écrire chaque objet sur une nouvelle ligne
    
    execution_date = context['ds']
    year, month, day = execution_date.split('-')
    hdfs_dir = f"/user/etudiant/crypto/raw/YYYY={year}/MM={month}/DD={day}"
    hdfs_file_path = f"{hdfs_dir}/yfinance_raw.json"
    subprocess.run(["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-mkdir", "-p", hdfs_dir])
    subprocess.run(["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-put", "-f", local_file, hdfs_file_path])

def store_in_hbase(**context):
    # Récupérer la date d'exécution
    execution_date = context['ds']
    year, month, day = execution_date.split('-')
    hdfs_output_path = f"hdfs:///user/etudiant/crypto/processed/YYYY={year}/MM={month}/DD={day}/part-00000"
    
    # Lire le fichier part-00000 depuis HDFS
    result = subprocess.run(
        ["docker", "exec", "-i", "-u", "root", "namenode", "hdfs", "dfs", "-cat", hdfs_output_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise ValueError(f"Erreur lors de la lecture de {hdfs_output_path}: {result.stderr}")
    
    # Les données sont au format JSON, une ligne par coin
    lines = result.stdout.strip().split('\n')
    transformed_data = [json.loads(line) for line in lines if line.strip()]

    # Connexion à HBase (assurez-vous que 'hbase' est le nom du conteneur accessible dans le réseau)
    connection = happybase.Connection('hbase', port=9090)
    
    # Créer la table si elle n'existe pas
    tables = connection.tables()
    if b'crypto_prices' not in tables:
        connection.create_table(
            'crypto_prices',
            {'stats': dict(max_versions=3)}  # Column Family 'stats' avec jusqu'à 3 versions
        )
    
    # Ouvrir la table
    table = connection.table('crypto_prices')
    
    # Insérer les données
    with table.batch() as batch:
        for record in transformed_data:
            coin = record['coin'].lower()  # Ex. 'bitcoin'
            row_key = f"{coin}_{execution_date}"  # Ex. 'bitcoin_2025-02-26'
            batch.put(row_key, {
                b'stats:price_min': str(record['min_price']).encode('utf-8'),
                b'stats:price_max': str(record['max_price']).encode('utf-8'),
                b'stats:price_avg': str(record['avg_price']).encode('utf-8'),
                b'stats:volume_sum': str(record['total_volume']).encode('utf-8'),
                b'stats:daily_variation_percent': str(record['daily_variation_percent']).encode('utf-8')
            })
    
    # Fermer la connexion
    connection.close()

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
    run_mapreduce = BashOperator(
        task_id='run_mapreduce',
        bash_command="""
        docker exec -i -u root namenode bash -c ' \
        cd /tmp && \
        cp /mnt/hadoop_data/mapreduce/mapper.py . && \
        cp /mnt/hadoop_data/mapreduce/reducer.py . && \
        chmod +x mapper.py reducer.py && \
        hdfs dfs -rm -r hdfs:///user/etudiant/crypto/processed/YYYY={{ ds_nodash[:4] }}/MM={{ ds_nodash[4:6] }}/DD={{ ds_nodash[6:] }} || true && \
        hadoop jar /opt/hadoop-3.2.1/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar \
        -files mapper.py,reducer.py \
        -mapper "python mapper.py" \
        -reducer "python reducer.py" \
        -input hdfs:///user/etudiant/crypto/raw/YYYY={{ ds_nodash[:4] }}/MM={{ ds_nodash[4:6] }}/DD={{ ds_nodash[6:] }}/yfinance_raw.json \
        -output hdfs:///user/etudiant/crypto/processed/YYYY={{ ds_nodash[:4] }}/MM={{ ds_nodash[4:6] }}/DD={{ ds_nodash[6:] }}'
        """
    )
    store_hbase = PythonOperator(
        task_id='store_in_hbase',
        python_callable=store_in_hbase,
        provide_context=True
    )

    fetch_data >> store_raw_data >> run_mapreduce >> store_hbase