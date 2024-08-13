from hydra.core.config_store import ConfigStore
from omegaconf import MISSING
from pydantic.dataclasses import dataclass

from jeffrey.config_schemas.infrastructure.gcp_schema import GCPConfig


@dataclass
class DataPreparingConfig:
    version: str = MISSING
    data_local_save_dir: str = "./data/raw"
    dvc_remote_repo: str = "https://github.com/jihoahn9303/data-versioning.git"
    dvc_data_folder: str = "data/raw"
    github_user_name: str = "jihoahn9303"
    github_access_token_secret_id: str = "jeffrey-data-github-access-token"
    infrastructure: GCPConfig = GCPConfig()


def setup_config() -> None:
    cs = ConfigStore.instance()
    cs.store(name="data_preparing_config_schema", node=DataPreparingConfig)