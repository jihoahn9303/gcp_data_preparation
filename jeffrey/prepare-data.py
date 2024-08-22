from pathlib import Path
from config_schemas.data_preparing_config_schema import DataPreparingConfig
from hydra.utils import instantiate
from dask.distributed import Client
from utils.utils import get_logger
from utils.config_utils import get_config
from utils.data_utils import get_raw_data_with_version
from utils.gcp_utils import access_secret_version


@get_config(config_path="../configs", config_name="data_preparing_config")  # type: ignore
def process_data(config: DataPreparingConfig) -> None:
    logger = get_logger(Path(__file__).name)
    logger.info("Processing raw data...")
    
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

        df = dataset_reader_manager.read_data().compute()
        sample_df = df.sample(n=5)

        for _, row in sample_df.iterrows():
            text = row["text"]
            cleaned_text = dataset_cleaner_manager(text)

            print(50 * "#")
            print(f"{text=}")
            print(f"{cleaned_text=}")
            print(50 * "#")

    finally:
        logger.info("Closing dask client and cluster...")
        client.close()
        cluster.close()

if __name__ == "__main__":
    process_data()
