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

import sys
sys.path.insert(0, '.')
import pytest
from pytest_mock import MockerFixture
from src.sdk.python.rtdip_sdk.pipelines.sources.spark.autoloader import DataBricksAutoLoaderSource
from tests.sdk.python.rtdip_sdk.pipelines._pipeline_utils.spark_configuration_constants import spark_session
from pyspark.sql import DataFrame, SparkSession

def test_databricks_autoloader_read_batch(spark_session: SparkSession):
    with pytest.raises(NotImplementedError) as excinfo:
        autoloader_source = DataBricksAutoLoaderSource(spark_session, {}, "/path", "parquet")
        autoloader_source.read_batch()
    assert str(excinfo.value) == 'Auto Loader only supports streaming reads. To perform a batch read, use the read_stream method and specify Trigger on the write_stream as `availableNow=True`' 

def test_databricks_autoloader_read_stream(spark_session: SparkSession, mocker: MockerFixture):
    autoloader_source = DataBricksAutoLoaderSource(spark_session, {}, "/path", "parquet")
    expected_df = spark_session.createDataFrame([{"a": "x"}])
    mocker.patch.object(autoloader_source, "spark", new_callable=mocker.PropertyMock(return_value=mocker.Mock(readStream=mocker.Mock(format=mocker.Mock(return_value=mocker.Mock(options=mocker.Mock(return_value=mocker.Mock(load=mocker.Mock(return_value=expected_df)))))))))
    assert autoloader_source.pre_read_validation()
    df = autoloader_source.read_stream()
    assert isinstance(df, DataFrame)
    assert autoloader_source.post_read_validation(df)