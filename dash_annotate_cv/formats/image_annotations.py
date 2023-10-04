from dash_annotate_cv.helpers import Xyxy, Xywh

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


            @property
            def area(self) -> float:
                """
                Compute area

                Returns:
                    float: Area of the bounding box
                """
                return abs(self.xyxy[2]-self.xyxy[0])*abs(self.xyxy[3]-self.xyxy[1])


            def ensure_valid_xyxy(self):
                """Ensure xyxy is valid
                """                
                self.xyxy = [
                    min(self.xyxy[0], self.xyxy[2]),
                    min(self.xyxy[1], self.xyxy[3]),
                    max(self.xyxy[0], self.xyxy[2]),
                    max(self.xyxy[1], self.xyxy[3])
                    ]


            @property
            def xywh(self) -> Xywh:
                """Get bbox in xywh format

                Returns:
                    Xywh: XYWH format (top left x, top left y, width, height)
                """                
                return [
                    self.xyxy[0],
                    self.xyxy[1],
                    abs(self.xyxy[2]-self.xyxy[0]),
                    abs(self.xyxy[3]-self.xyxy[1])
                    ]

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
        history_bboxs: Optional[List[BboxHistory]] = None
        history_labels: Optional[List[Label]] = None

        # Width
        image_width: Optional[int] = None

        # Height
        image_height: Optional[int] = None

        class Config(BaseConfig):
            omit_none = True


    # Image name to annotation
    image_to_entry: Dict[str,Annotation]


    @classmethod
    def new(cls):
        """Create a new empty annotation
        """
        return cls(image_to_entry={})


    def get_or_add_image(self, image_name: str, img_width: Optional[int], img_height: Optional[int]) -> Annotation:
        if image_name in self.image_to_entry:
            ann = self.image_to_entry[image_name]
            if ann.bboxs is None:
                ann.bboxs = []
        else:
            ann = ImageAnnotations.Annotation(
                image_name=image_name,
                bboxs=None,
                image_width=img_width,
                image_height=img_height
                )
            self.image_to_entry[image_name] = ann
        return ann