from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from typing import Optional, Any
from enum import Enum
import json
import os

@dataclass
class AnnotationStorage(DataClassDictMixin):
    """Specification for where to store annotations
    """        

    class Type(Enum):
        NONE = "none"
        JSON = "json"

    class StorageFrequency(Enum):
        EVERY_IMAGE = "every_image"
        EVERY_N_IMAGES = "every_n_images"

    # Storage type
    storage_type: Type = Type.NONE

    # JSON storage
    json_file: Optional[str] = None

    # Storage frequency
    storage_frequency: StorageFrequency = StorageFrequency.EVERY_IMAGE

    # Storage frequency (if storage_frequency is StorageFrequency.EVERY_N_IMAGES)
    storage_frequency_every_n: int = 10

    def __post_init__(self):
        if self.storage_type == AnnotationStorage.Type.NONE:
            pass
        elif self.storage_type == AnnotationStorage.Type.JSON:
            assert self.json_file is not None, "json_file must be set if storage_type is JSON"
        else:
            raise NotImplementedError


class AnnotationWriter:
    """Annotation writer
    """

    def __init__(self, storage: AnnotationStorage):
        self.storage = storage
        self._ctr_write = 0

    def write(self, annotations: Any):
        """Write annotations

        Args:
            annotations (Any): Annotations to write
        """                
        self._ctr_write += 1
        if self.storage.storage_type == AnnotationStorage.Type.NONE:
            return
        elif self.storage.storage_type == AnnotationStorage.Type.JSON:
            assert self.storage.json_file is not None, "json_file must be set if storage_type is JSON"

            # Check frequency
            write_every = self.storage.storage_frequency == AnnotationStorage.StorageFrequency.EVERY_IMAGE
            write_every_n = self.storage.storage_frequency == AnnotationStorage.StorageFrequency.EVERY_N_IMAGES and self._ctr_write % self.storage.storage_frequency_every_n == 0
            if write_every or write_every_n:

                # Write to file
                dir_name = os.path.dirname(self.storage.json_file)
                if dir_name != "":
                    assert os.path.exists(dir_name), f"Directory of json_file does not exist: {dir_name}"
                with open(self.storage.json_file,"w") as f:
                    json.dump(annotations.to_dict(), f, indent=3)

        else:
            raise NotImplementedError