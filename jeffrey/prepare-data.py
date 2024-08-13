from hydra.utils import instantiate

from jeffrey.config_schemas.data_preparing_config_schema import DataPreparingConfig
from jeffrey.utils.config_utils import get_config
from jeffrey.utils.data_utils import get_raw_data_with_version
from jeffrey.utils.gcp_utils import access_secret_version


@get_config(config_path="../configs", config_name="data_preparing_config")
def process_data(config: DataPreparingConfig) -> None:
    github_access_token = access_secret_version(
        project_id=config.infrastructure.project_id,
        secret_id=config.github_access_token_secret_id,
        version_id=config.access_token_secret_version
    )
    
    get_raw_data_with_version(
        version=config.data_version,
        data_local_save_dir=config.data_local_save_dir,
        dvc_remote_repo=config.dvc_remote_repo,
        dvc_data_folder=config.dvc_data_folder,
        github_user_name=config.github_user_name,
        github_access_token=github_access_token
    )
    
    dataset_reader_manager = instantiate(config.dataset_reader_manager)
    df = dataset_reader_manager.read_data()
    
    print(df.head())
    
if __name__ == "__main__":
    process_data()  # type: ignore