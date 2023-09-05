from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from enum import Enum
from typing import Optional, List, Iterator, Tuple
from PIL import Image
import os

class IndexBelowError(Exception):
    pass

class IndexAboveError(Exception):
    pass

@dataclass
class ImageSource:

    class Type(Enum):
        DEFAULT = "default"
        FOLDER = "folder"
        LIST_OF_FILES = "list_of_files"

    source_type: Type = Type.DEFAULT
    images: Optional[List[Tuple[str,Image.Image]]] = None
    folder_name: Optional[str] = None
    folder_pattern: str = "*.jpg"
    list_of_files: Optional[List[str]] = None

    def __post_init__(self):
        if self.source_type == ImageSource.Type.DEFAULT:
            assert self.images is not None, "images must be set if source_type is DEFAULT"
        elif self.source_type == ImageSource.Type.FOLDER:
            assert self.folder_name is not None, "folder_name must be set if source_type is FOLDER"
        elif self.source_type == ImageSource.Type.LIST_OF_FILES:
            assert self.list_of_files is not None, "list_of_files must be set if source_type is LIST_OF_FILES"
        else:
            raise NotImplementedError

class ImageIterator:
    def __init__(self, image_source: ImageSource):
        self.image_source = image_source
        self.idx_of_curr_img = -1

        self._file_names = None
        if image_source.source_type == ImageSource.Type.FOLDER:
            import glob
            assert image_source.folder_name is not None, "folder_name must be set if source_type is FOLDER"
            self._file_names = glob.glob(os.path.join(image_source.folder_name,image_source.folder_pattern))
            self._no_images = len(self._file_names)
        elif image_source.source_type == ImageSource.Type.LIST_OF_FILES:
            assert image_source.list_of_files is not None, "list_of_files must be set if source_type is LIST_OF_FILES"
            self._file_names = image_source.list_of_files
            self._no_images = len(self._file_names)
        else:
            assert image_source.images is not None, "images must be set if source_type is DEFAULT"
            self._no_images = len(image_source.images)
    
    def _image_at_idx(self, idx: int) -> Tuple[str,Image.Image]:
        print("Loading image at index", idx)
        if self.image_source.source_type == ImageSource.Type.DEFAULT:
            assert self.image_source.images is not None, "images must be set if source_type is DEFAULT"
            return self.image_source.images[idx]
        else:
            assert self._file_names is not None, "file_names must be set if source_type is not DEFAULT"
            return self._file_names[idx], Image.open(self._file_names[idx])

    def next(self) -> Tuple[str,Image.Image]:
        if self.idx_of_curr_img >= self._no_images-1:
            self.idx_of_curr_img = self._no_images
            raise IndexAboveError
        
        self.idx_of_curr_img += 1
        if self.idx_of_curr_img >= self._no_images:
            raise IndexAboveError
        result = self._image_at_idx(self.idx_of_curr_img)

        return result

    def prev(self) -> Tuple[str,Image.Image]:
        if self.idx_of_curr_img <= 0:
            self.idx_of_curr_img = -1
            raise IndexBelowError
        
        self.idx_of_curr_img -= 1
        result = self._image_at_idx(self.idx_of_curr_img)
        return result

    def __iter__(self):
        return self