from pyspark.sql.dataframe import DataFrame
from pyspark.sql import SparkSession
import pandas as pd
import numpy as np
import featuretools as ft


class EntityColumn:
    def __init__(self, entity_id: str, column_name: str):
        self.entity_id = entity_id
        self.column_name = column_name


class EntitySpark:
    def __init__(self,
                 entity_id: str,
                 df: DataFrame,
                 index: str = None,
                 variable_types: dict = None,
                 make_index: bool = False,
                 time_index: str = None,
                 secondary_time_index: str = None):
        self.entity_id = entity_id
        self.df = df
        self.index = index
        self.variable_types = variable_types
        self.make_index = make_index
        self.time_index = time_index
        self.secondary_time_index = secondary_time_index

    def drop_data(self):
        return EntitySparkWithoutData(self.entity_id, self.df.columns, self.index, self.variable_types, self.make_index,
                                      self.time_index, self.secondary_time_index)

    def __getitem__(self, column: str):
        columns = self.df.columns
        if column in columns:
            return EntityColumn(self.entity_id, column)
        raise KeyError("Column {0} doesn't exist in {1}".format(column, self.entity_id))


class EntitySparkWithoutData:
    def __init__(self,
                 entity_id: str,
                 columns: list,
                 index: str = None,
                 variable_types: dict = None,
                 make_index: bool = False,
                 time_index: str = None,
                 secondary_time_index: str = None):
        self.entity_id = entity_id
        self.columns = columns
        self.index = index
        self.variable_types = variable_types
        self.make_index = make_index
        self.time_index = time_index
        self.secondary_time_index = secondary_time_index


class Relationship:
    def __init__(self, parent_variable: EntityColumn, child_variable: EntityColumn):
        self.parent_variable = parent_variable
        self.child_variable = child_variable


class EntitySetSpark:
    """
    todo Current known limitations:
    1. Different entities should NOT have same columns. How to solve this?
    """

    def __init__(self, id: str):
        self.id = id
        self.entity_dict = {}
        self.relationships = []

    def entity_from_dataframe(self,
                              entity_id: str,
                              dataframe: DataFrame,
                              index: str = None,
                              variable_types: dict = None,
                              make_index: bool = False,
                              time_index: str = None,
                              secondary_time_index: str = None):
        entity = EntitySpark(entity_id, dataframe, index, variable_types, make_index, time_index, secondary_time_index)
        self._validate_spark_entity(entity)
        self.entity_dict[entity_id] = entity

    def get_big_df(self):
        scanned_cols = set()

        if len(self.relationships) == 0:
            raise ValueError("No relationships defined in {0}!".format(self.id))

        relationship = self.relationships[0]
        parent_entity = relationship.parent_variable.entity_id
        parent_col = relationship.parent_variable.column_name
        child_entity = relationship.child_variable.entity_id
        child_col = relationship.child_variable.column_name
        scanned_cols.add(parent_col)
        scanned_cols.add(child_col)
        parent_df = self.entity_dict[parent_entity].df
        child_df = self.entity_dict[child_entity].df

        if parent_col == child_col:
            res = parent_df.join(child_df, on=[parent_col])
        else:
            res = parent_df.join(child_df, parent_df[parent_col] == child_df[child_col])

        if len(self.relationships) > 1:
            for relationship in self.relationships[1:]:
                parent_entity = relationship.parent_variable.entity_id
                parent_col = relationship.parent_variable.column_name
                child_entity = relationship.child_variable.entity_id
                child_col = relationship.child_variable.column_name
                parent_df = self.entity_dict[parent_entity].df
                child_df = self.entity_dict[child_entity].df
                if parent_col == child_col:
                    sub_res = parent_df.join(child_df, on=[parent_col])
                else:
                    sub_res = parent_df.join(child_df, parent_df[parent_col] == child_df[child_col])
                if parent_col in scanned_cols:
                    res = res.join(sub_res, [parent_col])
                    scanned_cols.add(child_col)
                elif child_col in scanned_cols:
                    res = res.join(sub_res, [child_col])
                    scanned_cols.add(parent_col)
                else:
                    raise RuntimeError("Neither {0} or {1} is in its previous relationships: {2}".format(parent_col,
                                                                                                         child_col,
                                                                                                         scanned_cols))
        return res

    def add_relationship(self, relationship: Relationship):
        parent_entity = relationship.parent_variable.entity_id
        child_entity = relationship.child_variable.entity_id
        if parent_entity not in self.entity_dict:
            raise KeyError("Parent entity {0} does not exist in {1}".format(parent_entity, self.id))
        if child_entity not in self.entity_dict:
            raise KeyError("Child entity {0} does not exist in {1}".format(child_entity, self.id))
        self.relationships.append(relationship)

    def __getitem__(self, entity_id):
        if entity_id in self.entity_dict:
            return self.entity_dict[entity_id]
        raise KeyError('Entity %s does not exist in %s' % (entity_id, self.id))

    @staticmethod
    def _validate_spark_entity(entity: EntitySpark):
        # 1. Validate the dataframe is not empty
        total_rows = entity.df.count()
        if total_rows == 0:
            raise ValueError("Given entity {0} contains 0 rows! ".format(entity.entity_id))

        # 2. Validate index and time_index column exist
        if entity.index not in entity.df.columns:
            raise ValueError("Index column '{0}' does not exist in entity {1}!".format(entity.index, entity.entity_id))
        if entity.time_index is not None and entity.time_index not in entity.df.columns:
            raise ValueError("Time index column '{0}' does not exist in entity {1}!".format(entity.time_index,
                                                                                            entity.entity_id))

        # 3. Validate that index column is unique
        if entity.index is not None:
            index_distinct_rows = entity.df.select(entity.index).distinct().count()
            if total_rows != index_distinct_rows:
                raise ValueError("Index column {0} for {3} is not unqiue! ({1} != {2})".format(entity.index, total_rows,
                                                                                               index_distinct_rows,
                                                                                               entity.entity_id))

        # todo 3. Validate that time index column can be converted into time
        # if entity.time_index is not None:
        #     entity.dataframe.withColumn(entity.time_index, from_unixtime(unix_timestamp(col(entity.time_index))))


def dfs(spark: SparkSession,
        entityset: EntitySetSpark,
        target_entity: str,
        primary_col: str,
        cutoff_time=None,
        agg_primitives: list = None,
        trans_primitives: list = None,
        max_depth=None,
        training_window=None,
        approximate=None,
        chunk_size=None,
        n_jobs=1,
        num_partition: int = None):
    big_df = entityset.get_big_df()
    n_partitions = num_partition if num_partition is not None else big_df.select(primary_col).distinct().count()
    repartitioned = big_df.repartition(n_partitions, primary_col)

    def run_single_partition(iterator,
                             all_columns: list,
                             es_id: str,
                             entities: list,
                             relationships: list):
        list_iter = list(iterator)

        if len(list_iter) > 0:
            data = pd.DataFrame(list_iter, columns=all_columns)

            es = ft.EntitySet(id=es_id)
            for entity in entities:
                columns = entity.columns
                df = data[columns].drop_duplicates()

                es.entity_from_dataframe(entity_id=entity.entity_id,
                                         dataframe=df,
                                         index=entity.index,
                                         variable_types=entity.variable_types,
                                         make_index=entity.make_index,
                                         time_index=entity.time_index,
                                         secondary_time_index=entity.secondary_time_index)

            for relationship in relationships:
                parent_entity = relationship.parent_variable.entity_id
                parent_col = relationship.parent_variable.column_name
                child_entity = relationship.child_variable.entity_id
                child_col = relationship.child_variable.column_name
                es.add_relationship(ft.Relationship(es[parent_entity][parent_col],
                                                    es[child_entity][child_col]))

            feature_matrix, feature_dfs = ft.dfs(entityset=es,
                                                 agg_primitives=agg_primitives,
                                                 trans_primitives=trans_primitives,
                                                 target_entity=target_entity,
                                                 cutoff_time=cutoff_time,
                                                 cutoff_time_in_index=False,
                                                 n_jobs=n_jobs,
                                                 max_depth=max_depth,
                                                 training_window=training_window,
                                                 approximate=approximate,
                                                 chunk_size=chunk_size)

            feature_matrix.reset_index(inplace=True)

            columns = sorted(feature_matrix.columns)
            res = []
            for i in range(feature_matrix.shape[0]):
                row_res = {}
                for col in columns:
                    value = feature_matrix.ix[i, col]

                    # convert Numpy types to Python types, otherwise it cannot be converted
                    # to Spark DataFrame.
                    if isinstance(value, np.int64):
                        value = int(value)
                    elif isinstance(value, np.float64):
                        value = float(value)

                    row_res[col] = value
                res.append(row_res)
            return res

        else:
            return []

    all_columns = big_df.columns
    es_id = entityset.id
    entities = [entityset.entity_dict[entity].drop_data() for entity in entityset.entity_dict]
    relationships = entityset.relationships
    rdd = repartitioned.rdd.mapPartitions(lambda iteration: run_single_partition(iteration, all_columns,
                                                                             es_id, entities, relationships))
    res_df = spark.createDataFrame(rdd)
    return res_df

