from typing import Any, Optional

from hydra.core.config_store import ConfigStore
from omegaconf import MISSING, SI
from pydantic.dataclasses import dataclass


@dataclass
class DatasetReaderConfig:
    _target_: str = MISSING
    dataset_dir: str = MISSING
    dataset_name: str = MISSING
    gcp_project_id: str = SI("${infrastructure.project_id}")
    gcp_secret_id: str = SI("${github_access_token_secret_id}")
    secret_version_id: str = SI("${infrastructure.secret_version}")
    dvc_remote_repo_address: str = SI("${dvc_remote_repo}")
    user_name: str = SI("${github_user_name}")
    data_version: str = SI("${data_version}")


@dataclass
class GHCDatasetReaderConfig(DatasetReaderConfig):
    _target_: str = "jeffrey.data_processing.dataset_readers.GHCDatasetReader"
    split_ratio: float = MISSING


@dataclass
class JigsawToxicCommentsDatasetReader(DatasetReaderConfig):
    _target_: str = "jeffrey.data_processing.dataset_readers.JigsawToxicCommentsDatasetReader"
    split_ratio: float = MISSING


@dataclass
class TwitterDatasetReader(DatasetReaderConfig):
    _target_: str = "jeffrey.data_processing.dataset_readers.TwitterDatasetReader"
    valid_split_ratio: float = MISSING
    test_split_ratio: float = MISSING


@dataclass
class DatasetReaderManagerConfig:
    _target_: str = "jeffrey.data_processing.dataset_readers.DatasetReaderManager"
    dataset_readers: Any = MISSING
    repartition: bool = True
    available_memory: Optional[float] = None


def register_config() -> None:
    cs = ConfigStore.instance()
    cs.store(name="dataset_reader_manager_schema", node=DatasetReaderManagerConfig, group="dataset_reader_manager")
    cs.store(
        name="ghc_dataset_reader_schema", node=GHCDatasetReaderConfig, group="dataset_reader_manager/dataset_reader"
    )
    cs.store(
        name="jtc_dataset_reader_schema",
        node=JigsawToxicCommentsDatasetReader,
        group="dataset_reader_manager/dataset_reader",
    )
    cs.store(
        name="twitter_dataset_reader_schema", node=TwitterDatasetReader, group="dataset_reader_manager/dataset_reader"
    )
