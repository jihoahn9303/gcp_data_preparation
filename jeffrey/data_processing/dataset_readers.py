import os

from abc import ABC, abstractmethod
from typing import Optional

import dask.dataframe as dd
from dvc.api import get_url

from dask_ml.model_selection import train_test_split
from jeffrey.utils.utils import get_logger
from jeffrey.utils.data_utils import repartition_dataframe, get_repo_address_with_access_token


class DatasetReader(ABC):
    required_columns = {"text", "label", "split", "dataset_name"}
    split_names = {"train", "valid", "test"}

    def __init__(
        self, 
        dataset_dir: str,
        dataset_name: str,
        gcp_project_id: str,
        gcp_secret_id: str,
        secret_version_id: str,
        dvc_remote_repo_address: str,
        user_name: str,
        data_version: str
    ) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.dataset_dir = dataset_dir
        self.dataset_name = dataset_name
        self.dvc_remote_repo = get_repo_address_with_access_token(
            gcp_project_id=gcp_project_id,
            gcp_secret_id=gcp_secret_id,
            secret_version_id=secret_version_id,
            repo_address=dvc_remote_repo_address,
            user_name=user_name
        )
        self.data_version = data_version
        
    def get_dask_dataframe_rows(self, df: dd.DataFrame) -> int:
        total_length = df.map_partitions(len).compute().sum()
        return total_length

    def read_data(self) -> dd.DataFrame:
        train_df, dev_df, test_df = self._read_data()

        df = self.assign_split_names_to_dataframes_and_merge(train_df, dev_df, test_df)
        df["dataset_name"] = self.dataset_name
        
        num_rows = self.get_dask_dataframe_rows(df)
        assert num_rows != 0

        if any(required_column not in df.columns.values for required_column in self.required_columns):
            raise ValueError(f"Dataset must contain all required columns: {self.required_columns}")

        # 메모리 자원 확인 or compute() 대신 다른 코드 사용 고려 -> 최적화 과정에서 indexerror가 발생?
        # unique_split_names = set(df["split"].drop_duplicates().compute().tolist())
        # if unique_split_names != self.split_names:
        #     raise ValueError(f"Dataset must contain all required split names: {self.split_names}")
        
        df_pd = df.compute()  # 전체 데이터프레임을 Pandas로 변환
        unique_split_names = set(df_pd["split"].unique())

        if len(unique_split_names) != len(self.split_names):
            raise ValueError(f"Dataset must contain all required split names: {self.split_names}")
        
        del df_pd
        return df[list(self.required_columns)]

    @abstractmethod
    def _read_data(self) -> tuple[dd.DataFrame, dd.DataFrame, dd.DataFrame]:
        """
        Read and split dataset into 3 splits: train, valid, test.
        If required, this function should make 'label' column.
        The return value must be a dd.DataFrame, with required columns: self.required_columns
        """
        pass

    def assign_split_names_to_dataframes_and_merge(
        self, train_df: dd.DataFrame, valid_df: dd.DataFrame, test_df: dd.DataFrame
    ) -> dd.DataFrame:
        train_df["split"] = "train"
        valid_df["split"] = "valid"
        test_df["split"] = "test"

        return dd.concat([train_df, valid_df, test_df])

    def split_dataset(
        self, df: dd.DataFrame, test_size: float, stratify_column: Optional[str] = None
    ) -> tuple[dd.DataFrame, dd.DataFrame]:
        if stratify_column is None:
            first_return_df: dd.DataFrame
            second_return_df: dd.DataFrame
            first_return_df, second_return_df = train_test_split(
                df, test_size=test_size, random_state=1234, shuffle=True
            )
            return first_return_df, second_return_df
        unique_column_values = df[stratify_column].unique()
        first_dfs, second_dfs = [], []

        for unique_column in unique_column_values:
            sub_df = df[df[stratify_column] == unique_column]
            sub_first_df, sub_second_df = train_test_split(sub_df, test_size=test_size, random_state=1234, shuffle=True)
            first_dfs.append(sub_first_df)
            second_dfs.append(sub_second_df)

        return dd.concat(first_dfs), dd.concat(second_dfs)

    def get_remote_data_url(self, dataset_path: str, dvc_remote_name: str = "gs-remote-storage") -> str:
        return get_url(
            path=dataset_path,
            repo=self.dvc_remote_repo,
            rev=self.data_version,
            remote=dvc_remote_name
        )

class GHCDatasetReader(DatasetReader):
    def __init__(
        self, 
        dataset_dir: str,
        dataset_name: str,
        split_ratio: float,
        gcp_project_id: str,
        gcp_secret_id: str,
        secret_version_id: str,
        dvc_remote_repo_address: str,
        user_name: str,
        data_version: str
    ) -> None:
        super().__init__(
            dataset_dir, 
            dataset_name,
            gcp_project_id,
            gcp_secret_id,
            secret_version_id,
            dvc_remote_repo_address,
            user_name,
            data_version
        )
        self.split_ratio = split_ratio

    def _read_data(self) -> tuple[dd.DataFrame, dd.DataFrame, dd.DataFrame]:
        self.logger.info("Reading GHC Dataset...")
        train_tsv_path = os.path.join(self.dataset_dir, "ghc_train.tsv")
        train_tsv_url = self.get_remote_data_url(dataset_path=train_tsv_path)
        train_df = dd.read_csv(train_tsv_url, sep="\t", header=0)

        test_tsv_path = os.path.join(self.dataset_dir, "ghc_test.tsv")
        test_tsv_url = self.get_remote_data_url(dataset_path=test_tsv_path)
        test_df = dd.read_csv(test_tsv_url, sep="\t", header=0)

        train_df["label"] = (train_df["hd"] + train_df["cv"] + train_df["vo"] > 0).astype(int)
        test_df["label"] = (test_df["hd"] + test_df["cv"] + test_df["vo"] > 0).astype(int)

        train_df, valid_df = self.split_dataset(df=train_df, test_size=self.split_ratio, stratify_column="label")

        return train_df, valid_df, test_df


class JigsawToxicCommentsDatasetReader(DatasetReader):
    def __init__(
        self, 
        dataset_dir: str,
        dataset_name: str,
        split_ratio: float,
        gcp_project_id: str,
        gcp_secret_id: str,
        secret_version_id: str,
        dvc_remote_repo_address: str,
        user_name: str,
        data_version: str
    ) -> None:
        super().__init__(
            dataset_dir, 
            dataset_name,
            gcp_project_id,
            gcp_secret_id,
            secret_version_id,
            dvc_remote_repo_address,
            user_name,
            data_version
        )
        self.split_ratio = split_ratio

    def get_text_and_label_columns(self, df: dd.DataFrame) -> dd.DataFrame:
        excluded_columns = ["id", "comment_text"]
        remaining_columns = df.columns.difference(excluded_columns).tolist()

        df["label"] = (df[remaining_columns].sum(axis=1) > 0).astype(int)
        df = df.rename(columns={"comment_text": "text"})

        return df

    def _read_data(self) -> tuple[dd.DataFrame, dd.DataFrame, dd.DataFrame]:
        self.logger.info("Reading Jigsaw toxic Dataset...")

        test_csv_path = os.path.join(self.dataset_dir, "test.csv")
        test_csv_url = self.get_remote_data_url(dataset_path=test_csv_path)
        test_df = dd.read_csv(test_csv_url)

        test_labels_csv_path = os.path.join(self.dataset_dir, "test_labels.csv")
        test_labels_csv_url = self.get_remote_data_url(dataset_path=test_labels_csv_path)
        test_labels_df = dd.read_csv(test_labels_csv_url)

        test_df = test_df.merge(test_labels_df, on=["id"])
        test_df = test_df[test_df["toxic"] != -1]
        test_df = self.get_text_and_label_columns(test_df)
        to_train_df, test_df = self.split_dataset(test_df, test_size=0.1, stratify_column="label")

        train_csv_path = os.path.join(self.dataset_dir, "train.csv")
        train_csv_url = self.get_remote_data_url(dataset_path=train_csv_path)
        train_df = dd.read_csv(train_csv_url)
        train_df = self.get_text_and_label_columns(train_df)
        train_df = dd.concat([train_df, to_train_df])

        train_df, valid_df = self.split_dataset(df=train_df, test_size=self.split_ratio, stratify_column="label")

        return train_df, valid_df, test_df


class TwitterDatasetReader(DatasetReader):
    def __init__(
        self, 
        dataset_dir: str, 
        dataset_name: str, 
        valid_split_ratio: float, 
        test_split_ratio: float,
        gcp_project_id: str,
        gcp_secret_id: str,
        secret_version_id: str,
        dvc_remote_repo_address: str,
        user_name: str,
        data_version: str
    ) -> None:
        super().__init__(
            dataset_dir, 
            dataset_name,
            gcp_project_id,
            gcp_secret_id,
            secret_version_id,
            dvc_remote_repo_address,
            user_name,
            data_version
        )
        self.valid_split_ratio = valid_split_ratio
        self.test_split_ratio = test_split_ratio

    @staticmethod
    def get_label_from_comment_text(text: str) -> int:
        if text == "not_cyberbullying":
            return 0
        else:
            return 1

    def get_text_and_label_columns(self, df: dd.DataFrame) -> dd.DataFrame:
        df["label"] = df["cyberbullying_type"].apply(
            lambda x: self.get_label_from_comment_text(x), meta=("x", "int64")
        )
        df = df.rename(columns={"tweet_text": "text"})

        excluded_columns = ["cyberbullying_type"]
        remaining_columns = df.columns.difference(excluded_columns).tolist()

        return df[remaining_columns]

    def _read_data(self) -> tuple[dd.DataFrame, dd.DataFrame, dd.DataFrame]:
        self.logger.info("Reading Twitter Dataset...")

        df_path = os.path.join(self.dataset_dir, "cyberbullying_tweets.csv")
        df_url = self.get_remote_data_url(dataset_path=df_path)
        df = dd.read_csv(df_url)
        df = self.get_text_and_label_columns(df)

        train_df, valid_df = self.split_dataset(df=df, test_size=self.valid_split_ratio, stratify_column="label")

        valid_df, test_df = self.split_dataset(df=valid_df, test_size=self.test_split_ratio, stratify_column="label")

        return train_df, valid_df, test_df


class DatasetReaderManager:
    def __init__(
        self, 
        dataset_readers: dict[str, DatasetReader], 
        repartition: bool = True,
        available_memory: Optional[float] = None
    ) -> None:
        self.dataset_readers = dataset_readers
        self.repartition = repartition
        self.available_memory = available_memory

    def read_data(self, n_workers: int) -> dd.DataFrame:
        dfs = [dataset_reader.read_data() for dataset_reader in self.dataset_readers.values()]
        df = dd.concat(dfs)
        if self.repartition:
            df = repartition_dataframe(
                df=df, 
                n_workers=n_workers, 
                available_memory=self.available_memory
            )
        return df
