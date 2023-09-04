from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from enum import Enum
from typing import Optional, List, Iterator
from PIL import Image
import os

@dataclass
class ImageSource(DataClassDictMixin):

    class Type(Enum):
        LOADED = "loaded"
        FOLDER = "folder"
        LIST_OF_FILES = "list_of_files"

    source_type: Type
    loaded: Optional[List[Image.Image]] = None
    folder_name: Optional[str] = None
    folder_pattern: str = "*.jpg"
    list_of_files: Optional[List[str]] = None

    def __post_init__(self):
        if self.source_type == ImageSource.Type.LOADED:
            assert self.loaded is not None, "loaded must be set if source_type is LOADED"
        elif self.source_type == ImageSource.Type.FOLDER:
            assert self.folder_name is not None, "folder_name must be set if source_type is FOLDER"
        elif self.source_type == ImageSource.Type.LIST_OF_FILES:
            assert self.list_of_files is not None, "list_of_files must be set if source_type is LIST_OF_FILES"
        else:
            raise NotImplementedError

    def iterate_over_images(self) -> Iterator[Image.Image]:
        if self.source_type == ImageSource.Type.LOADED:
            assert self.loaded is not None, "loaded must be set if source_type is LOADED"
            for image in self.loaded:
                yield image
        elif self.source_type == ImageSource.Type.FOLDER:
            import glob
            assert self.folder_name is not None, "folder_name must be set if source_type is FOLDER"
            for filename in glob.glob(os.path.join(self.folder_name,self.folder_pattern)):
                yield Image.open(filename)
        elif self.source_type == ImageSource.Type.LIST_OF_FILES:
            assert self.list_of_files is not None, "list_of_files must be set if source_type is LIST_OF_FILES"
            for filename in self.list_of_files:
                yield Image.open(filename)
        else:
            raise NotImplementedError