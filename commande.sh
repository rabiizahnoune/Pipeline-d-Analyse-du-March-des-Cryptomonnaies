#intialiser base de donnes
docker-compose run --rm airflow-webserver airflow db init

docker-compose run --rm airflow-scheduler airflow db init




docker exec -it airflow-webserver airflow users create --username admin --firstname Rabii --lastname Zahoune --role Admin --email admin@example.com --password admin






docker run big_data_projet-scraper bash -c "python /app/scraper.py"

docker run -it big_data_projet-mapreduce bash


docker exec -u root -it hadoop-namenode bash
