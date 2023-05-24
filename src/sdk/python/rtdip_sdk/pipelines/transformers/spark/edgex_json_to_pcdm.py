# Copyright 2022 RTDIP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pyspark.sql import DataFrame
from pyspark.sql.functions import from_json, col, explode, when, lit, coalesce, to_timestamp, from_unixtime

from ..interfaces import TransformerInterface
from ..._pipeline_utils.models import Libraries, SystemType
from ..._pipeline_utils.spark import EDGEX_SCHEMA

class EdgeXJsonToPCDMTransformer(TransformerInterface):
    '''
    Converts a Spark Dataframe column containing a json string created by EdgeX to the Process Control Data Model

    Args:
        data (DataFrame): Dataframe containing the column with EdgeX data
        status_null_value (str): If populated, will replace 'Good' in the Status column with the specified value.
        change_type_value (str): If populated, will replace 'insert' in the ChangeType column with the specified value.
    '''
    data: DataFrame
    status_null_value: str
    change_type_value: str

    def __init__(self, data: DataFrame, status_null_value: str = "Good", change_type_value: str = "insert") -> None: 
        self.data = data
        self.status_null_value = status_null_value
        self.change_type_value = change_type_value

    @staticmethod
    def system_type():
        '''
        Attributes:
            SystemType (Environment): Requires PYSPARK
        '''
        return SystemType.PYSPARK

    @staticmethod
    def libraries():
        libraries = Libraries()
        return libraries
    
    @staticmethod
    def settings() -> dict:
        return {}
    
    def pre_transform_validation(self):
        return True
    
    def post_transform_validation(self):
        return True
    
    def transform(self) -> DataFrame:
        '''
        Returns:
            DataFrame: A dataframe with the specified column converted to PCDM
        '''
        df = (
            self.data
                .withColumn("body", from_json("body", EDGEX_SCHEMA))
                .select("*", explode("body.readings"))
                .selectExpr("body.deviceName as TagName", "to_utc_timestamp(to_timestamp((col.origin / 1000000000)), current_timezone()) as EventTime", "col.value as Value", "col.valueType as ValueType")
                .withColumn("Status", lit(self.status_null_value))
                .withColumn("ChangeType", lit(self.change_type_value))
                .withColumn("ValueType", (when(col("ValueType") == "Int8", "integer")
                                        .when(col("ValueType") == "Int16", "integer")
                                        .when(col("ValueType") == "Int32", "integer")
                                        .when(col("ValueType") == "Int64", "integer")
                                        .when(col("ValueType") == "Uint8", "integer")
                                        .when(col("ValueType") == "Uint16", "integer")
                                        .when(col("ValueType") == "Uint32", "integer")
                                        .when(col("ValueType") == "Uint64", "integer")
                                        .when(col("ValueType") == "Float32", "float")
                                        .when(col("ValueType") == "Float64", "float")
                                        .when(col("ValueType") == "Bool", "bool")
                                        .otherwise("string")))
        )
        
        return df.select("TagName", "EventTime", "Status", "Value", "ValueType", "ChangeType") 