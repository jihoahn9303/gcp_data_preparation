from hydra.core.config_store import ConfigStore
from omegaconf import MISSING
from pydantic.dataclasses import dataclass

from config_schemas.data_processing import dataset_readers_schema, dataset_cleaners_schema
from config_schemas.infrastructure import gcp_schema


@dataclass
class DataPreparingConfig:
    data_version: str = MISSING
    data_local_save_dir: str = "./data/raw"
    dvc_remote_repo: str = "https://github.com/jihoahn9303/data-versioning.git"
    dvc_data_folder: str = "data/raw"
    github_user_name: str = "jihoahn9303"
    github_access_token_secret_id: str = "jeffrey-data-github-access-token"
    access_token_secret_version: str = MISSING
    infrastructure: gcp_schema.GCPConfig = gcp_schema.GCPConfig()
    dataset_reader_manager: dataset_readers_schema.DatasetReaderManagerConfig = MISSING
    dataset_cleaner_manager: dataset_cleaners_schema.DatasetCleanerManagerConfig = MISSING


def setup_config() -> None:
    gcp_schema.register_config()
    dataset_readers_schema.register_config()
    dataset_cleaners_schema.register_config()
    
    cs = ConfigStore.instance()
    cs.store(name="data_preparing_config_schema", node=DataPreparingConfig)