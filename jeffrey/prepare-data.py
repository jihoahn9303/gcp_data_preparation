import os
import gc
from pathlib import Path
from config_schemas.data_preparing_config_schema import DataPreparingConfig
from hydra.utils import instantiate
import dask.dataframe as dd
from dask.distributed import Client
from utils.utils import get_logger
from utils.config_utils import get_config
from utils.data_utils import get_raw_data_with_version
from utils.gcp_utils import access_secret_version
from data_processing.dataset_cleaners import DatasetCleanerManager


def process_raw_data(
    df_partition: dd.DataFrame, 
    dataset_cleaner_manager: DatasetCleanerManager
) -> dd.Series:
    result = df_partition["text"].apply(dataset_cleaner_manager)
    del df_partition
    gc.collect()
    return result


@get_config(config_path="../configs", config_name="data_preparing_config")  # type: ignore
def process_data(config: DataPreparingConfig) -> None:
    logger = get_logger(Path(__file__).name)
    logger.info("Processing raw data...")
    
    processed_data_save_dir = config.processed_data_save_dir
    
    cluster = instantiate(config.dask_cluster)
    client = Client(cluster)
    
    try:
        github_access_token = access_secret_version(
            project_id=config.infrastructure.project_id,
            secret_id=config.github_access_token_secret_id,
            version_id=config.access_token_secret_version,
        )

        get_raw_data_with_version(
            version=config.data_version,
            data_local_save_dir=config.data_local_save_dir,
            dvc_remote_repo=config.dvc_remote_repo,
            dvc_data_folder=config.dvc_data_folder,
            github_user_name=config.github_user_name,
            github_access_token=github_access_token,
        )

        dataset_reader_manager = instantiate(config.dataset_reader_manager)
        dataset_cleaner_manager = instantiate(config.dataset_cleaner_manager)

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
        
        df[df["split"] == "train"].to_parquet(train_parquet_path)
        df[df["split"] == "valid"].to_parquet(valid_parquet_path)
        df[df["split"] == "test"].to_parquet(test_parquet_path)
        
        logger.info("Data processing finished!")

    finally:
        logger.info("Closing dask client and cluster...")
        client.close()
        cluster.close()

if __name__ == "__main__":
    process_data()
