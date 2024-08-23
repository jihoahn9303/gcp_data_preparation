from hydra.core.config_store import ConfigStore
from pydantic.dataclasses import dataclass


@dataclass
class GCPConfig:
    project_id: str = "e2eml-jiho-430901"
    secret_version: str = "v1"
    zone: str = "asia-northeast3-a"
    network: str = "default"


def register_config() -> None:
    cs = ConfigStore.instance()
    cs.store(name="gcp_config_schema", node=GCPConfig)
