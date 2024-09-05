import os
from pathlib import Path

from hydra.utils import instantiate
import dask.dataframe as dd
from dask.distributed import Client

from jeffrey.config_schemas.data_preparing_config_schema import DataPreparingConfig
from jeffrey.utils.data_utils import filter_based_on_min_words
from jeffrey.utils.io_utils import write_yaml_file
from jeffrey.utils.utils import get_logger
from jeffrey.utils.config_utils import get_pickle_config, custom_instantiate
from jeffrey.data_processing.dataset_cleaners import DatasetCleanerManager


def process_raw_data(
    df_partition: dd.DataFrame, 
    dataset_cleaner_manager: DatasetCleanerManager
) -> dd.Series:
    return df_partition["text"].apply(dataset_cleaner_manager)


@get_pickle_config(config_path="jeffrey/configs/automatically_generated", config_name="data_preparing_config")  # type: ignore
def process_data(config: DataPreparingConfig) -> None:
    logger = get_logger(Path(__file__).name)
    logger.info("Processing raw data...")
    
    processed_data_save_dir = config.processed_data_save_dir
    
    logger.info("Instantiate dask cluster and client...")
    cluster = custom_instantiate(config.dask_cluster)
    client = Client(cluster, timeout=7200)
    
    try:
        dataset_reader_manager = instantiate(config.dataset_reader_manager)
        dataset_cleaner_manager = instantiate(config.dataset_cleaner_manager)

        logger.info("Reading data across workers...")
        df = dataset_reader_manager.read_data(n_workers=config.dask_cluster.n_workers)
    
        logger.info("Persisting data across workers...")
        df = df.persist()  # 데이터를 클러스터의 워커 메모리에 고정
        
        logger.info("Cleaning data...")
        df = df.assign(
            cleaned_text=df.map_partitions(
                process_raw_data, 
                dataset_cleaner_manager=dataset_cleaner_manager,
                meta=("text", "object")
            )    
        )
        df = df.compute()
        
        train_parquet_path = os.path.join(processed_data_save_dir, "train.parquet")
        valid_parquet_path = os.path.join(processed_data_save_dir, "valid.parquet")
        test_parquet_path = os.path.join(processed_data_save_dir, "test.parquet")
        
        train_df = df[df["split"] == "train"]
        valid_df = df[df["split"] == "valid"]
        test_df = df[df["split"] == "test"]
        
        train_df = filter_based_on_min_words(train_df, min_words=config.min_words)
        valid_df = filter_based_on_min_words(valid_df, min_words=config.min_words)
        test_df = filter_based_on_min_words(test_df, min_words=config.min_words)
        
        train_df.to_parquet(train_parquet_path)
        valid_df.to_parquet(valid_parquet_path)
        test_df.to_parquet(test_parquet_path)
        
        docker_info = {"docker_image": config.docker_image_name, "docker_tag": config.docker_image_tag}
        docker_info_save_path = os.path.join(processed_data_save_dir, "docker_info.yaml")
        write_yaml_file(yaml_file_path=docker_info_save_path, yaml_file_content=docker_info)
        
        logger.info("Data processing finished!")

    finally:
        logger.info("Closing dask client and cluster...")
        client.close()
        cluster.close()

if __name__ == "__main__":
    process_data()
