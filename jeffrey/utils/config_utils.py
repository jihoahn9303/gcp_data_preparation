import argparse
import importlib
from dataclasses import asdict
from io import BytesIO, StringIO
from functools import partial
import logging
import logging.config

import os
import pickle
from typing import Any, Optional

import hydra
import yaml
from hydra import initialize, compose

from jeffrey.config_schemas import data_preparing_config_schema, tokenizer_training_config_schema
from hydra.types import TaskFunction
from omegaconf import DictConfig, OmegaConf

from jeffrey.utils.io_utils import open_file


def get_config(config_path: str, config_name: str) -> TaskFunction:
    setup_config()
    setup_logger()

    def main_decorator(task_function: TaskFunction) -> Any:
        @hydra.main(config_path=config_path, config_name=config_name, version_base="1.3")
        def decorated_main(dict_config: Optional[DictConfig]) -> Any:
            config = OmegaConf.to_object(dict_config)
            return task_function(config)
        return decorated_main
    
    return main_decorator

def get_pickle_config(config_path: str, config_name: str) -> TaskFunction:
    setup_config()
    setup_logger()
    
    def main_decorator(task_function: TaskFunction) -> Any:
        def decorated_main() -> Any:
            config = load_pickle_config(config_path, config_name)
            return task_function(config)  
        return decorated_main
    
    return main_decorator

def load_pickle_config(config_path: str, config_name: str) -> Any:
    with open_file(os.path.join(config_path, f"{config_name}.pickle"), "rb") as f:
        config = pickle.load(f)
    return config

def setup_config() -> None:
    data_preparing_config_schema.setup_config()
    tokenizer_training_config_schema.setup_config()

def setup_logger() -> None:
    try:
        with open("./jeffrey/configs/hydra/job_logging/custom.yaml", "r") as stream:
            config = yaml.load(stream, Loader=yaml.FullLoader)
    except:
        with open("/app/jeffrey/configs/hydra/job_logging/custom.yaml", "r") as stream:
            config = yaml.load(stream, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)
    
def config_args_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("--config-path", type=str, default="../configs/", help="Directory of the config files")
    parser.add_argument("--config-name", type=str, required=True, help="Name of the config file")
    parser.add_argument("--overrides", nargs="*", help="Hydra config overrides", default=[])

    return parser.parse_args()

def compose_config(config_path: str, config_name: str, overrides: Optional[list[str]] = None) -> Any:
    setup_config()
    setup_logger()

    if overrides is None:
        overrides = []

    with initialize(version_base=None, config_path=config_path, job_name="config-compose"):
        dict_config = compose(config_name=config_name, overrides=overrides)
        config = OmegaConf.to_object(dict_config)
    return config

# def save_config_as_yaml(config: Any, save_path: str) -> None:
#     text_io = StringIO()
#     OmegaConf.save(config, text_io, resolve=True)
#     with open_file(save_path, "w") as f:
#         f.write(text_io.getvalue())

def enforce_int_types(config):
    """
    Traverse the configuration and enforce specific fields to be integers.
    """
    if isinstance(config, dict):
        for key, value in config.items():
            if key == "nthreads" and isinstance(value, str):
                # Convert 'nthreads' to integer if it's in string format
                try:
                    config[key] = int(value)
                except ValueError:
                    print(f"Warning: Failed to convert {key} to integer. Keeping as string.")
            elif isinstance(value, (dict, list)):
                enforce_int_types(value)
    elif isinstance(config, list):
        for item in config:
            enforce_int_types(item)
            
def save_config_as_yaml(config: Any, save_path: str) -> None:
    # Ensure config is a DictConfig object; if not, attempt to convert
    if not isinstance(config, DictConfig):
        try:
            config = OmegaConf.create(config)  # Convert to DictConfig if possible
        except ValueError:
            raise ValueError("Provided config is not a valid format for OmegaConf conversion.")

    # Convert DictConfig object to a dict to ensure types are correctly enforced
    config_dict = OmegaConf.to_container(config, resolve=True)

    # Enforce integer types where necessary
    enforce_int_types(config_dict)

    # Save the corrected config as YAML
    with open(save_path, 'w') as f:
        yaml.dump(config_dict, f)

def save_config_as_pickle(config: Any, save_path: str) -> None:
    bytes_io = BytesIO()
    pickle.dump(config, bytes_io)
    with open_file(save_path, "wb") as f:
        f.write(bytes_io.getvalue())
        
def custom_instantiate(config: Any) -> Any:
    config_as_dict = asdict(config)
    
    if "_target_" not in config_as_dict:
        raise ValueError("Config does not have _target_ key")

    _target_ = config_as_dict["_target_"]
    _partial_ = config_as_dict.get("_partial_", False)

    config_as_dict.pop("_target_", None)
    config_as_dict.pop("_partial_", None)

    splitted_target = _target_.split(".")
    module_name, class_name = ".".join(splitted_target[:-1]), splitted_target[-1]

    module = importlib.import_module(module_name)
    _class = getattr(module, class_name)
    if _partial_:
        return partial(_class, **config_as_dict)
    return _class(**config_as_dict)