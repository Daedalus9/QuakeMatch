FROM docker.elastic.co/elasticsearch/elasticsearch:7.17.0
ENV ES_JAVA_OPTS="-Xms1g -Xmx1g"
RUN sysctl -w vm.max_map_count=262144
EXPOSE 9200 9300
CMD ["elasticsearch"]
