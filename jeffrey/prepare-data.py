from jeffrey.config_schemas.config_schema import Config
from jeffrey.utils.config_utils import get_config
from jeffrey.utils.data_utils import get_raw_data_with_version
from jeffrey.utils.gcp_utils import access_secret_version


@get_config(config_path="../configs", config_name="config")
def process_data(config: Config) -> None:
    version = "v1"
    data_local_save_dir = "./data/raw"
    dvc_remote_repo = "https://github.com/jihoahn9303/data-versioning.git"
    dvc_data_folder = "data/raw"
    github_user_name = "jihoahn9303"
    github_access_token = access_secret_version(
        project_id="e2eml-jiho-430901",
        secret_id="jeffrey-data-github-access-token",
        version_id="1"
    )
    
    get_raw_data_with_version(
        version=version,
        data_local_save_dir=data_local_save_dir,
        dvc_remote_repo=dvc_remote_repo,
        dvc_data_folder=dvc_data_folder,
        github_user_name=github_user_name,
        github_access_token=github_access_token
    )
    
    
if __name__ == "__main__":
    process_data()  # type: ignore