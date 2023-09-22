from typing import List, Optional, Dict
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
            """Single label
            """        
            # Single label
            single: Optional[str] = None

            # Multiple labels
            multiple: Optional[List[str]] = None

            # Timestamp
            timestamp: Optional[float] = None

            # Author
            author: Optional[str] = None

            class Config(BaseConfig):
                omit_none = True

        # Image name
        image_name: str

        # Label
        label: Label

        # History
        history: Optional[List[Label]] = None
        
        class Config(BaseConfig):
            omit_none = True

    # Image name to annotation
    image_to_entry: Dict[str,Annotation]
