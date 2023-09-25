from typing import List, Optional, Dict, Union
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig

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
            xyxy: List[Union[float,int]]

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

        # Image name
        image_name: str

        # Label
        label: Optional[Label] = None

        # Bounding boxes
        bboxs: Optional[List[Bbox]] = None

        # History
        history: Optional[List[Union[Label,Bbox]]] = None
        
        class Config(BaseConfig):
            omit_none = True

    # Image name to annotation
    image_to_entry: Dict[str,Annotation]


    @classmethod
    def new(cls):
        """Create a new empty annotation
        """
        return cls(image_to_entry={})