from dash_annotate_cv.formats import ImageAnnotations
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from typing import Optional, Any, List
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class StorageType(Enum):
    JSON = "json"
    COCO = "coco"


@dataclass
class AnnotationStorage(DataClassDictMixin):
    """Specification for where to store annotations
    """        

    class StorageFrequency(Enum):
        EVERY_OPERATION = "every_operation"
        EVERY_N_OPERATIONS = "every_n_operations"

    # Storage type
    storage_types: List[StorageType] = []

    # JSON storage
    json_file: Optional[str] = None

    # COCO storage
    coco_file: Optional[str] = None

    # Storage frequency
    storage_frequency: StorageFrequency = StorageFrequency.EVERY_OPERATION

    # Storage frequency (if storage_frequency is StorageFrequency.EVERY_N_IMAGES)
    storage_frequency_every_n: int = 10

    def __post_init__(self):
        if StorageType.JSON in self.storage_types:
            assert self.json_file is not None, "json_file must be set if storage_type is JSON"
        if StorageType.COCO in self.storage_types:
            assert self.coco_file is not None, "coco_file must be set if storage_type is COCO"

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
        # Check if any storage types requested         
        if len(self.storage.storage_types) == 0:
            return

        # Update ctr
        self._ctr_write += 1
        
        # Check if frequency matches
        write_every = self.storage.storage_frequency == AnnotationStorage.StorageFrequency.EVERY_OPERATION
        write_every_n = self.storage.storage_frequency == AnnotationStorage.StorageFrequency.EVERY_N_OPERATIONS and self._ctr_write % self.storage.storage_frequency_every_n == 0
        write = write_every or write_every_n
        if not write:
            return
        
        # Write
        if StorageType.JSON in self.storage.storage_types:
            assert self.storage.json_file is not None, "json_file must be set if storage_type is JSON"
            from dash_annotate_cv.formats.default import write_default_json
            write_default_json(annotations, self.storage.json_file)

        if StorageType.COCO in self.storage.storage_types:
            assert self.storage.coco_file is not None, "coco_file must be set if storage_type is COCO"
            from dash_annotate_cv.formats.coco import write_to_coco
            write_to_coco(annotations, self.storage.coco_file)


def load_image_anns_from_storage(storage: AnnotationStorage) -> Optional[ImageAnnotations]:
    if len(storage.storage_types) == 0:
        return None
    for storage_type in storage.storage_types:
        anns = load_image_anns_if_exist(storage_type, json_file=storage.json_file, coco_file=storage.coco_file)
        if anns is not None:
            return anns
    return None


def load_image_anns_if_exist(storage_type: StorageType, json_file: Optional[str] = None, coco_file: Optional[str] = None) -> Optional[ImageAnnotations]:
    """Load image annotations if they exist

    Args:
        storage_type (StorageType): Storage type
        json_file (Optional[str], optional): JSON file. Defaults to None.
        coco_file (Optional[str], optional): COCO file. Defaults to None.

    Returns:
        Optional[ImageAnnotations]: Image annotations if they exist
    """    
    if storage_type == StorageType.JSON:
        assert json_file is not None, "json_file must be set if storage_type is JSON"
        from dash_annotate_cv.formats.default import load_from_default_json_if_exist
        return load_from_default_json_if_exist(json_file)
    elif storage_type == StorageType.COCO:
        assert coco_file is not None, "coco_file must be set if storage_type is COCO"
        from dash_annotate_cv.formats.coco import load_from_coco_if_exist
        return load_from_coco_if_exist(coco_file)
    else:
        raise NotImplementedError(f"storage_type {storage_type} not implemented")