import logging
import socket
import subprocess
import pkg_resources

from symspellpy import SymSpell


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"[{socket.gethostname()}] {name}")

def run_shell_command(cmd: str) -> str:
    return subprocess.run(cmd, text=True, shell=True, check=True, capture_output=True).stdout


class SpellCorrectionModel:
    def __init__(
        self,
        max_dictionary_edit_distance: int = 2,
        prefix_length: int = 7,
        count_threshold: int = 1
    ) -> None:
        self.dictionary_path = pkg_resources.resource_filename(
            package_or_requirement="symspellpy",
            resource_name="frequency_dictionary_en_82_765.txt"
        )
        self.bigram_dictionary_path = pkg_resources.resource_filename(
            package_or_requirement="symspellpy",
            resource_name="frequency_bigramdictionary_en_243_342.txt"
        )
        self.max_dictionary_edit_distance = max_dictionary_edit_distance
        self.prefix_length = prefix_length
        self.count_threshold = count_threshold
        
        self.model = self._initialize_model()
        
    def _initialize_model(self) -> SymSpell:
        model = SymSpell(
            max_dictionary_edit_distance=self.max_dictionary_edit_distance,
            prefix_length=self.prefix_length,
            count_threshold=self.count_threshold
        )
        model.load_dictionary(
            corpus=self.dictionary_path,
            term_index=0,
            count_index=1
        )
        model.load_bigram_dictionary(
            corpus=self.bigram_dictionary_path,
            term_index=0,
            count_index=2
        )
        
        return model
    
    def __call__(self, text: str) -> str:
        return self.model.lookup_compound(
            phrase=text, 
            max_edit_distance=self.max_dictionary_edit_distance
        )[0].term