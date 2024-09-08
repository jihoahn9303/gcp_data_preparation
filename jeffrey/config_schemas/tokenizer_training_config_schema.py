from hydra.core.config_store import ConfigStore
from omegaconf import MISSING
from pydantic.dataclasses import dataclass

from jeffrey.config_schemas.infrastructure import gcp_schema
from jeffrey.config_schemas.tokenization import tokenizer_schema


@dataclass
class TokenizerTrainingConfig:
    infrastructure: gcp_schema.GCPConfig = gcp_schema.GCPConfig()
    docker_image_name: str = MISSING
    docker_image_tag: str = MISSING
    data_parquet_path: str = MISSING
    text_column_name: str = MISSING
    tokenizer: tokenizer_schema.TokenizerConfig = MISSING


def setup_config() -> None:
    gcp_schema.register_config()
    tokenizer_schema.register_config()

    cs = ConfigStore.instance()
    cs.store(name="tokenizer_training_config_schema", node=TokenizerTrainingConfig)
