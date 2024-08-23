from shutil import rmtree
from typing import Optional

import psutil
import dask.dataframe as dd

from utils.utils import run_shell_command


def get_cmd_to_get_raw_data(
    version: str,
    data_local_save_dir: str,
    dvc_remote_repo: str,
    dvc_data_folder: str,
    github_user_name: str,
    github_access_token: str,
) -> str:
    """Get shell command to download the raw data from dvc store

    Parameters
    ----------
    version: str
        data version
    data_local_save_dir: str
        where to save the downloaded data locally
    dvc_remote_repo: str
        dvc repository that holds information about the data
    dvc_data_folder: str
        location where the remote data is stored
    github_user_name: str
        github user name
    github_access_token: str
        github access token

    Returns
    -------
    str
        shell command to download the raw data from dvc store
    """
    without_https = dvc_remote_repo.replace("https://", "")
    dvc_remote_repo = f"https://{github_user_name}:{github_access_token}@{without_https}"
    command = f"dvc get {dvc_remote_repo} {dvc_data_folder} --rev {version} -o {data_local_save_dir}"

    return command


def get_raw_data_with_version(
    version: str,
    data_local_save_dir: str,
    dvc_remote_repo: str,
    dvc_data_folder: str,
    github_user_name: str,
    github_access_token: str,
) -> None:
    rmtree(data_local_save_dir, ignore_errors=True)
    command = get_cmd_to_get_raw_data(
        version=version,
        data_local_save_dir=data_local_save_dir,
        dvc_remote_repo=dvc_remote_repo,
        dvc_data_folder=dvc_data_folder,
        github_user_name=github_user_name,
        github_access_token=github_access_token,
    )
    run_shell_command(cmd=command)

def get_npartitions(
    df_memory_usage: int,
    n_workers: int,
    available_memory: Optional[float],
    min_partition_size: int,
    aimed_nrof_partitions_per_worker: int,
) -> int:
    # 가용 메모리 설정
    total_available_memory = (available_memory * n_workers if available_memory is not None 
                              else psutil.virtual_memory().available)
    
    # 예외 처리: 메모리 사용량이 최소 파티션 크기 이하인 경우
    if df_memory_usage <= min_partition_size:
        return 1

    # 예외 처리: 워커 수에 따른 파티션 크기가 최소 크기 이하인 경우
    if df_memory_usage / n_workers <= min_partition_size:
        return round(df_memory_usage / min_partition_size)
    
    # 파티션 계산
    nrof_partitions_per_worker = max(1, int(df_memory_usage / total_available_memory))
    nrof_partitions = nrof_partitions_per_worker * n_workers

    # 파티션 수 조정
    while (df_memory_usage / (nrof_partitions + 1)) > min_partition_size and (
        nrof_partitions // n_workers
    ) < aimed_nrof_partitions_per_worker:
        nrof_partitions += 1

    return nrof_partitions


def repartition_dataframe(
    df: dd.DataFrame,
    n_workers: int,
    available_memory: Optional[float] = None,
    min_partition_size: int = 10 * 1024**2,
    aimed_nrof_partitions_per_worker: int = 10,
) -> dd.DataFrame:
    df_memory_usage = df.memory_usage(deep=True).sum().compute()
    nrof_partitions = get_npartitions(
        df_memory_usage, n_workers, available_memory, min_partition_size, aimed_nrof_partitions_per_worker
    )
    partitioned_df: dd.DataFrame = df.repartition(npartitions=1).repartition(npartitions=nrof_partitions)  # type: ignore
    return partitioned_df