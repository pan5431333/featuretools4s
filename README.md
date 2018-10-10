## FeatureTools for Spark (featuretools4s)

### 1. What's FeatureTools? 
FeatureTools is a Python library open-sourced by MIT's 
FeatureLab aiming to automate 
the process of feature engineering in Machine Learning 
applications. 

Please visit the [official website](https://docs.featuretools.com/index.html)
for more details about FeatureTools. 

*FeatureTools4S* is a Python library written by me aiming to scale 
FeatureTools with **Spark**, making it capable of generating 
features for billions of rows of data, which is usually 
considered impossible to process on single machine using 
original FeatureTools library with Pandas. 

*FeatureTools4S* provides **almost the same** API as original 
FeatureTools, which make its users completely free of transferring 
between FeatureTools and FeatureTools4S. **Hence we suggest the readers 
first to learn FeatureTools and then you can easily work on FeatureTools4S.**

### 2. How to use FeatureTools4S? 
First install *featuretools4s* through pip: 
```bash
pip3 install featuretools4s 
```  

Then a simple example of using *featuretools4s* is as follows: 
```python
import featuretools4s as fts
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
```