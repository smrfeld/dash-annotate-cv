from dash_annotate_cv.helpers import Xyxy

from typing import List, Optional, Dict, Union
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig
import datetime
from enum import Enum
import logging


logger = logging.getLogger(__name__)


@dataclass
class ImageAnnotations(DataClassDictMixin):
    """Image annotations result
    """        


    @dataclass
    class Annotation(DataClassDictMixin):
        """Annotation for a single image
        """        


        @dataclass
        class Label(DataClassDictMixin):
            """Label
            """        

            # Single label
            single: Optional[str] = None

            # Multiple labels
            multiple: Optional[List[str]] = None

            # Timestamp
            timestamp: Optional[float] = None

            # Author
            author: Optional[str] = None

            # Equality
            def __eq__(self, other):
                if not isinstance(other, ImageAnnotations.Annotation.Label):
                    return False
                return self.single == other.single and self.multiple == other.multiple

            class Config(BaseConfig):
                omit_none = True


        @dataclass
        class Bbox(DataClassDictMixin):
            """Bounding box
            """ 

            # Bounding box in [xlower,ylower,xupper,yupper] format
            xyxy: Xyxy

            # Label
            class_name: Optional[str] = None

            # Timestamp
            timestamp: Optional[float] = None

            # Author
            author: Optional[str] = None

            # Equality
            def __eq__(self, other):
                if not isinstance(other, ImageAnnotations.Annotation.Bbox):
                    return False
                return self.xyxy == other.xyxy and self.class_name == other.class_name

            class Config(BaseConfig):
                omit_none = True


        @dataclass
        class BboxHistory(DataClassDictMixin):

            class Operation(Enum):
                ADD = "add"
                DELETE = "delete"
                UPDATE = "update"

            # Operation
            operation: Operation

            # Bbox
            bbox: "ImageAnnotations.Annotation.Bbox"
        

        # Image name
        image_name: str

        # Label
        label: Optional[Label] = None

        # Bounding boxes
        bboxs: Optional[List[Bbox]] = None

        # History
        history: Optional[List[Union[Label,BboxHistory]]] = None

        class Config(BaseConfig):
            omit_none = True


    # Image name to annotation
    image_to_entry: Dict[str,Annotation]


    @classmethod
    def new(cls):
        """Create a new empty annotation
        """
        return cls(image_to_entry={})


    def get_or_add_image(self, image_name: str, with_bboxs: bool) -> Annotation:
        if image_name in self.image_to_entry:
            ann = self.image_to_entry[image_name]
            if ann.bboxs is None:
                ann.bboxs = []
        else:
            ann = ImageAnnotations.Annotation(
                image_name=image_name,
                bboxs=[]
                )
            self.image_to_entry[image_name] = ann
        return ann