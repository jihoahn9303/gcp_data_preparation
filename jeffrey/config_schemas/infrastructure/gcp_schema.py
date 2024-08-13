from pydantic.dataclasses import dataclass
from hydra.core.config_store import ConfigStore


@dataclass
class GCPConfig:
    project_id: str = "e2eml-jiho-430901"
    secret_version: str = "v1"
    
    
def register_config() -> None:
    cs = ConfigStore.instance()
    cs.store(name="gcp_config_schema", node=GCPConfig)