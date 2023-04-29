from pyspark.sql import *
from pyspark.sql.functions import *
import re
from pyspark.sql.types import *
spark = SparkSession.builder.master("local[*]").appName("test").getOrCreate()

spark.sparkContext.setLogLevel("OFF")

data="C:\\bigdata\\drivers\\complexxmldata.xml"
df=spark.read.format("xml").option("rowTag","catalog_item").option("path","C:\\bigdata\\drivers\\complexxmldata.xml").load()
def flatten_json(df):
    # compute Complex Fields (Lists and Structs) in Schema
    complex_fields = dict([(field.name, field.dataType)
                                for field in df.schema.fields
                                if type(field.dataType) == ArrayType or  type(field.dataType) == StructType])
    while len(complex_fields)!=0:
        col_name=list(complex_fields.keys())[0]
        print ("Processing :"+col_name+" Type : "+str(type(complex_fields[col_name])))
        # if StructType then convert all sub element to columns.
        # i.e. flatten structs
        if (type(complex_fields[col_name]) == StructType):
            #expanded = [col(col_name+'.'+k).alias(col_name+'_'+k) for k in [ n.name for n in  complex_fields[col_name]]]
            expanded = [col(col_name+'.'+k).alias(k) for k in [ n.name for n in  complex_fields[col_name]]]
            df=df.select("*", *expanded).drop(col_name)
        # if ArrayType then add the Array Elements as Rows using the explode function
        # i.e. explode Arrays
        elif (type(complex_fields[col_name]) == ArrayType):
            df=df.withColumn(col_name, explode_outer(col_name))
        # recompute remaining Complex Fields in Schema
        complex_fields = dict([(field.name, field.dataType)
                                for field in df.schema.fields
                                if type(field.dataType) == ArrayType or  type(field.dataType) == StructType])

    return df.toDF(*[re.sub("[^a-zA-Z0-9]","",x) for x in df.columns])

df=flatten_json(df)
df.createOrReplaceTempView("tab")
res=spark.sql("select gender, count(*) cnt from tab group by gender order by cnt desc")
res.show()
#df.printSchema()