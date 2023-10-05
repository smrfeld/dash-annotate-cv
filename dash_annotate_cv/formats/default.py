from dash_annotate_cv.formats.image_annotations import ImageAnnotations

import json
import os
from typing import Optional
import logging


logger = logging.getLogger(__name__)


def write_default_json(anns: ImageAnnotations, fname_output_json: str):
    
    if os.path.dirname(fname_output_json) != "":
        os.makedirs(os.path.dirname(fname_output_json), exist_ok=True)
        logger.debug(f"Created directory {os.path.dirname(fname_output_json)}")
    with open(fname_output_json,'w') as f:        
        json.dump(anns.to_dict(), f, indent=3)
        logger.debug(f"Wrote to {fname_output_json}")


def load_from_default_json_if_exist(fname_json: str) -> Optional[ImageAnnotations]:
    if not os.path.exists(fname_json):
        return None
    with open(fname_json,'r') as f:
        return ImageAnnotations.from_dict(json.load(f))
