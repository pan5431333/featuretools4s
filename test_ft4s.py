import featuretools4s.featuretools4s as fts
from pyspark.sql import SparkSession

import os
import pandas as pd

os.environ["SPARK_HOME"] = "C:\Python36\Lib\site-packages\pyspark"
os.environ["PATH"] = "C:\Python36;" + os.environ["PATH"]
pd.set_option('display.expand_frame_repr', False)
spark = SparkSession.builder.master("local[*]").getOrCreate()

order_df = spark.read.csv("resources/order.csv", header=True, inferSchema=True).sort("sales_tax")
customer_df = spark.read.csv("resources/customer.csv", header=True, inferSchema=True)

es = fts.EntitySetSpark(id="test")
es.entity_from_dataframe("order", order_df, index="order_num", time_index="wo_timestamp")
es.entity_from_dataframe("customer", customer_df, index="cust_num")
es.add_relationship(fts.Relationship(es["customer"]["cust_num"], es["order"]["cust_num"]))

features = fts.dfs(spark, entityset=es, target_entity="customer", primary_col="cust_num", num_partition=5)
features.show()
