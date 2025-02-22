# from airflow import DAG
# from airflow.operators.bash import BashOperator
# from datetime import datetime

# default_args = {
#     "owner": "airflow",
#     "start_date": datetime(2024, 1, 1),
#     "retries": 1,
# }

# with DAG(
#     "crypto_pipeline",
#     default_args=default_args,
#     schedule_interval="@daily",
#     catchup=False,
# ) as dag:

#     scrape_task = BashOperator(
#         task_id="scrape_data",
#         bash_command="docker exec scraper python /app/scraper.py",
#     )

#     process_task = BashOperator(
#         task_id="process_data",
#         bash_command="docker exec mapreduce python /app/process.py",
#     )

#     load_task = BashOperator(
#         task_id="load_data",
#         bash_command="docker exec loader python /app/load_to_hbase.py",
#     )

#     # Définition de l'ordre des tâches
#     scrape_task >> process_task >> load_task
# # from airflow import DAG
# # from airflow.operators.python_operator import PythonOperator
# # from airflow.operators.bash import BashOperator

# # from datetime import datetime
# # import yfinance as yf
# # import pandas as pd
# # import numpy as np
# # import ta  # Pour les indicateurs techniques



# # # -------------------- Définition du DAG --------------------
# # default_args = {
# #     'owner': 'airflow',
# #     'start_date': datetime(2024, 1, 1),
# # }

# # dag = DAG(
# #     'gold_data_dag',
# #     default_args=default_args,
# #     description='Un DAG pour récupérer et traiter les données de l\'or',
# #     schedule_interval='@daily',  # Cela exécute le DAG tous les jours
# #     catchup=False,  # Ne pas exécuter les DAGs passés lors du démarrage
# # )

# # runer_task = BashOperator(
# #     task_id = 'runer',
# #     bash_command = 'docker start scraper',
# #     dag=dag
# # )

# # hello_task = BashOperator(
# #     task_id='say_hello',
# #     bash_command='docker exec -it scraper python /app/scraper.py',
# #     dag=dag,
# # )

# # # Exécution de la tâche
# # runer_task >> hello_task




# from airflow import DAG
# from airflow.operators.bash import BashOperator
# from datetime import datetime

# # -------------------- Définition du DAG --------------------
# default_args = {
#     'owner': 'airflow',
#     'start_date': datetime(2024, 1, 1),
# }

# dag = DAG(
#     'gold_data_dag',
#     default_args=default_args,
#     description='Un DAG pour récupérer et traiter les données de l\'or',
#     schedule_interval='@daily',  # Cela exécute le DAG tous les jours
#     catchup=False,  # Ne pas exécuter les DAGs passés lors du démarrage
# )

# # Tâche pour démarrer le conteneur Docker
# ingestion_data = BashOperator(
#     task_id='runer',
#     bash_command='docker run big_data_projet-scraper bash -c "python /app/scraper.py"',
#     dag=dag,
# )

# traitment_de_donnes = BashOperator(
#     task_id = 'traiter',
#     bash_command = 'docker run big_data_projet-mapreduce bash -c "python /app/mapper.py"',
#     dag = dag
# )

# # Définir l'ordre d'exécution des tâches
# ingestion_data >> traitment_de_donnes
