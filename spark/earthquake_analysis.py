from pyspark.sql import SparkSession
from pyspark.sql.functions import col, split, regexp_replace, trim, substring_index, expr, concat_ws, transform, explode, when, size, to_timestamp, unix_timestamp, monotonically_increasing_id, lit, date_format
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType
from elasticsearch import Elasticsearch

spark = SparkSession.builder.appName("KafkaSparkIntegration") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2") \
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
    .getOrCreate()

kafka_df = spark.read.format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "earthquakes") \
    .option("startingOffsets", "earliest") \
    .load()

decoded_df = kafka_df.selectExpr("CAST(value AS STRING) as message") \
    .select(
        split(col("message"), "\\];\\[").alias("values")
    ) \
    .withColumn("timestamps", split(regexp_replace(col("values")[0], '[\"\']', ''), ", ")) \
    .withColumn("regions", split(regexp_replace(col("values")[1], '[\"\']', ';'), ";, ")) \
    .withColumn("regions", expr("transform(regions, x -> regexp_replace(x, ';', ''))")) \
    .withColumn("latitudes", split(regexp_replace(col("values")[2], '[\"\']', ''), ", ")) \
    .withColumn("longitudes", split(regexp_replace(col("values")[3], '[\"\']', ''), ", ")) \
    .withColumn("magnitudes", split(regexp_replace(col("values")[4], '[\"\']', ''), ", ")) \
    .withColumn("row_index", explode(expr("sequence(0, size(timestamps)-1)"))) \
    .withColumn("timestamp", when(col("row_index") == 0, substring_index(col("timestamps")[col("row_index").cast("int")], "[", -1)) \
                               .otherwise(col("timestamps")[col("row_index").cast("int")])) \
    .withColumn("region", col("regions")[col("row_index").cast("int")]) \
    .withColumn("latitude", col("latitudes")[col("row_index").cast("int")]) \
    .withColumn("longitude", col("longitudes")[col("row_index").cast("int")]) \
    .withColumn("magnitude", when(col("row_index") == size(col("magnitudes")) - 1, substring_index(col("magnitudes")[col("row_index").cast("int")], "]", 1)) \
                             .otherwise(col("magnitudes")[col("row_index").cast("int")])) \
    .withColumn("latitude_antipode", expr("-latitude")) \
    .withColumn("longitude_antipode", when(col("longitude") < 0, 180 + col("longitude")).otherwise(col("longitude") - 180))

decoded_df = decoded_df.withColumn("timestamp", substring_index(col("timestamp"), ".", 1))

decoded_df = decoded_df.orderBy(col("timestamp").desc())

decoded_df = decoded_df.withColumn("id", monotonically_increasing_id())

decoded_df = decoded_df.filter(col("magnitude").cast("float") >= 5.5)

decoded_df = decoded_df.withColumn("timestamp_antipode", expr("timestamp + INTERVAL 3 DAYS"))

antipode_matches = decoded_df.alias("main").join(
    decoded_df.alias("antipode"),
    (col("main.latitude_antipode").between(col("antipode.latitude") - 30, col("antipode.latitude") + 30)) &
    (col("main.longitude_antipode").between(col("antipode.longitude") - 30, col("antipode.longitude") + 30)) &
    (col("main.timestamp_antipode") <= col("antipode.timestamp")) &
    (col("antipode.timestamp") <= col("main.timestamp_antipode") + expr("INTERVAL 3 DAYS")),
    "left_outer"
).where(
    (col("main.id") != col("antipode.id"))
).groupBy("main.id").agg(expr("concat_ws(';', collect_list(antipode.id))").alias("matches"))

decoded_df = decoded_df.join(antipode_matches, ["id"], "left_outer").na.fill({"matches": ""})
decoded_df = decoded_df.orderBy(col("id").asc())
decoded_df = decoded_df.withColumn("timestamp", date_format(col("timestamp"), "yyyy-MM-dd HH:mm:ss.SSS"))
decoded_df = decoded_df.select("id", "timestamp", "region", "latitude", "longitude", "magnitude", "latitude_antipode", "longitude_antipode", "matches")
decoded_df = decoded_df.repartition(1)

decoded_df.write.mode("overwrite").csv("output", header=True)

es_nodes = "elasticsearch:9200"
es_index = "earthquakes"
es_mapping = "earthquake_mapping"

es = Elasticsearch([es_nodes])
es_write_conf = {
    "es.nodes": es_nodes,
    "es.resource": f"{es_index}/{es_mapping}",
    "es.mapping.id": "id",
    "es.nodes.wan.only": "true"
}

schema = StructType([
    StructField("id", StringType(), False),
    StructField("timestamp", TimestampType(), False),
    StructField("region", StringType(), False),
    StructField("latitude", FloatType(), False),
    StructField("longitude", FloatType(), False),
    StructField("magnitude", FloatType(), False),
    StructField("latitude_antipode", FloatType(), False),
    StructField("longitude_antipode", FloatType(), False),
    StructField("matches", StringType(), False)
])

decoded_df.write \
    .format("org.elasticsearch.spark.sql") \
    .options(**es_write_conf) \
    .option("es.nodes.wan.only", "true") \
    .option("es.mapping.id", "id") \
    .save()

spark.stop()