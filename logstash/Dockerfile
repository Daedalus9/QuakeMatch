FROM docker.elastic.co/logstash/logstash:8.8.1@sha256:9b2e080605e208ef1165fd6cfd68a8b05c2031c8818b8520f82f73238dbb471c

COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf

COPY seismic_portal_links.txt /usr/share/logstash/seismic_portal_links.txt

RUN logstash-plugin install logstash-filter-xml
RUN logstash-plugin install logstash-filter-mutate
RUN logstash-plugin install logstash-input-http

CMD ["-f", "/usr/share/logstash/pipeline/logstash.conf"]
