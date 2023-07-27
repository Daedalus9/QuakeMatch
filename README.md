# QuakeMatch
![QuakeMatch](https://github.com/Daedalus9/QuakeMatch/assets/50534107/f0de1c54-ba7f-46a0-ab32-c4ad00e6b26e)


## :twisted_rightwards_arrows: QuakeMatch Pipeline
![QuakeMatch Pipeline](https://github.com/Daedalus9/QuakeMatch/assets/50534107/21fcd7c9-1762-45da-8a8e-aed7e15b7468)


## :bar_chart: Kibana Dashboard
![Kibana](https://github.com/Daedalus9/QuakeMatch/assets/50534107/eec68964-ff00-4630-9f45-3998e94b6037)


## :notebook: Requirements
- Docker
- python
- wget
- A solution with, at least, 16GB of RAM

## :zap: Usage
- Install Docker in your system, than run the following command for create a docker network:
```bash
docker network create kafka-network
```
- Create a container with Kafka Zookeeper: 
```bash
docker run -d \
  --name zookeeper \
  --network kafka-network \
  -p 2181:2181 \
  -e ZOOKEEPER_CLIENT_PORT=2181 \
  confluentinc/cp-zookeeper:latest
```

- Wait Zookeper to be fully loaded, then create a container with Kafka:
```bash
docker run -d \
  --name kafka \
  --network kafka-network \
  -p 9092:9092 \
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  confluentinc/cp-kafka:latest
```
And a container with Kafka UI:
```bash
docker run -d \
  --name kafka-ui \
  --network kafka-network \
  -p 8080:8080 \
  -e KAFKA_CLUSTERS_0_NAME=local \
  -e KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka:9092 \
  -e KAFKA_CLUSTERS_0_ZOOKEEPER=zookeeper:2181 \
  -e KAFKA_CLUSTERS_0_ENABLESR=false \
  -e KAFKA_CLUSTERS_0_SASLMECHANISM= \
  -e KAFKA_CLUSTERS_0_SASLPLAIN_USERNAME= \
  -e KAFKA_CLUSTERS_0_SASLPLAIN_PASSWORD= \
  -e KAFKA_CLUSTERS_0_SASLPLAIN_PASSWORD_FILE= \
  -e KAFKA_CLUSTERS_0_TRUSTEDCERTS= \
  -e KAFKA_CLUSTERS_0_CLIENTCERT= \
  -e KAFKA_CLUSTERS_0_CLIENTKEY= \
  -e KAFKA_CLUSTERS_0_CLIENTKEYPASSWORD= \
  -e KAFKA_CLUSTERS_0_CONSUMERCONFIGS= \
  -e KAFKA_CLUSTERS_0_ADMINCONFIGS= \
  provectuslabs/kafka-ui:latest
```

- Go to elasticsearch folder and create a docker image:
```bash
docker build -t elastic-image .
```
Then run Elasticsearch:
```bash
docker run -d --name elasticsearch --network kafka-network -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" elastic-image
```

- Create a Kibana container:
 ```bash
docker run -d --name kibana -p 5601:5601 --network kafka-network -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" docker.elastic.co/kibana/kibana:7.15.1
```

- Go to logstash/urls_dates.py, in section
```bash
start_date = datetime.datetime(YYYY, M, DD)
end_date = datetime.datetime(YYYY, M, DD)
```
Replace YYYY, M, DD  with the date you want to consider (start_date < end_date)

- Run python script:
```bash
python3 urls_dates.py
```

- Create a docker image of Logstash:
```bash
docker build -t logstash-image .
```
Then run Logstash:
```bash
docker run -d --name logstash-container --network kafka-network  logstash-image
```

- Go to spark folder, then run:
```bash
wget https://repo1.maven.org/maven2/org/elasticsearch/elasticsearch-spark-20_2.12/7.15.1/elasticsearch-spark-20_2.12-7.15.1.jar
```
And
```bash
wget https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.1/spark-sql-kafka-0-10_2.12-3.4.1.jar
```

- Create a docker image of Apache Spark:
```bash
docker build -t spark-earthquakes .
```

- Wait until all messages in Kafka's "earthquakes" topic are ready, then run Apache Spark container
```bash
docker run -d --network kafka-network --name spark-earthquakes_analyzer spark-earthquakes
```

- In the browser, put the url "http://localhost:5601", go to "Kibana / Saved Objects", click on "import" and select "export.ndjson" in kibana folder

- Open left menu in Kibana, select Dashboard, select the imported dashboard for see all lens
