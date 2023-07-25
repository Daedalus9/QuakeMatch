FROM bitnami/spark:latest

WORKDIR /app
COPY earthquake_analysis.py .
COPY requirements.txt .
COPY elasticsearch-spark-20_2.12-7.15.1.jar /opt/bitnami/spark/jars/

RUN pip install -r requirements.txt

CMD ["python", "earthquake_analysis.py"]
