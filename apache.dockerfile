FROM apache/airflow:2.7.0


RUN pip install --upgrade pip
RUN pip install yfinance ta hdfs3
