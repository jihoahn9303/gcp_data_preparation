from typing import Any

from hydra.core.config_store import ConfigStore
from omegaconf import MISSING
from pydantic.dataclasses import dataclass


@dataclass
class DatasetReaderConfig:
    _target_: str = MISSING
    dataset_dir: str = MISSING
    dataset_name: str = MISSING


@dataclass
class GHCDatasetReaderConfig(DatasetReaderConfig):
    _target_: str = "data_processing.dataset_readers.GHCDatasetReader"
    split_ratio: float = MISSING


@dataclass
class JigsawToxicCommentsDatasetReader(DatasetReaderConfig):
    _target_: str = "data_processing.dataset_readers.JigsawToxicCommentsDatasetReader"
    split_ratio: float = MISSING


@dataclass
class TwitterDatasetReader(DatasetReaderConfig):
    _target_: str = "data_processing.dataset_readers.TwitterDatasetReader"
    valid_split_ratio: float = MISSING
    test_split_ratio: float = MISSING


@dataclass
class DatasetReaderManagerConfig:
    _target_: str = "data_processing.dataset_readers.DatasetReaderManager"
    dataset_readers: Any = MISSING


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
