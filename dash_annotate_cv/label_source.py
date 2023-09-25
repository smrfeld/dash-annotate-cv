from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from mashumaro import DataClassDictMixin


@dataclass
class LabelSource(DataClassDictMixin):
    """Specification for where to get labels from
    """

    class Type(Enum):
        DEFAULT = "default"
        JSON_FILE = "json_file"
        TXT_FILE = "txt_file"

    # Source type
    source_type: Type = Type.DEFAULT

    # Default source: list of labels
    labels: Optional[List[str]] = None

    # JSON file source
    json_file: Optional[str] = None

    # TXT file source
    txt_file: Optional[str] = None

    def __post_init__(self):
        if self.source_type == LabelSource.Type.DEFAULT:
            assert self.labels is not None, "labels must be set if source_type is DEFAULT"
        elif self.source_type == LabelSource.Type.JSON_FILE:
            assert self.json_file is not None, "json_file must be set if source_type is JSON_FILE"
        elif self.source_type == LabelSource.Type.TXT_FILE:
            assert self.txt_file is not None, "txt_file must be set if source_type is TXT_FILE"
        else:
            raise NotImplementedError

    def get_labels(self) -> List[str]:
        """Get the possible labels

        Returns:
            List[str]: List of possible labels
        """        
        if self.source_type == LabelSource.Type.DEFAULT:
            assert self.labels is not None, "labels must be set if source_type is DEFAULT"
            return self.labels
        elif self.source_type == LabelSource.Type.JSON_FILE:
            import json
            assert self.json_file is not None, "json_file must be set if source_type is JSON_FILE"
            with open(self.json_file) as f:
                data = json.load(f)
                assert type(data) == list, "JSON file must contain a list of strings"
                assert all([type(item) == str for item in data]), "JSON file must contain a list of strings"
                return data
        elif self.source_type == LabelSource.Type.TXT_FILE:
            assert self.txt_file is not None, "txt_file must be set if source_type is TXT_FILE"
            with open(self.txt_file) as f:
                data = [line.strip() for line in f.readlines()]
                assert type(data) == list, "TXT file must contain a list of strings"
                assert all([type(item) == str for item in data]), "TXT file must contain a list of strings"
                return data
        else:
            raise NotImplementedError