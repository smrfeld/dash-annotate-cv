from dash_annotate_cv.formats.image_annotations import ImageAnnotations

import json
import os
from typing import Dict
import logging


logger = logging.getLogger(__name__)


def write_to_coco(anns: ImageAnnotations, fname_output_json: str):
    assert os.path.splitext(fname_output_json)[1] == '.json', "fname_output_json must be a json file"

    image_id_next = 1
    ann_id_next = 1
    cat_id_next = 1
    coco_dct: Dict = {"images": [], "annotations": [], "categories": []}
    for anns_for_img in anns.image_to_entry.values():

        # Add image
        img = {
            "id": image_id_next,
            "width": anns_for_img.image_width,
            "height": anns_for_img.image_height,
            "file_name": anns_for_img.image_name
            }
        coco_dct["images"].append(img)
        image_id_next += 1
        image_id = image_id_next - 1

        # Add annotations
        for bbox in anns_for_img.bboxs or []:

            # Add category if needed or get category id
            if bbox.class_name not in [cat["name"] for cat in coco_dct["categories"]]:
                cat = {
                    "id": cat_id_next,
                    "name": bbox.class_name,
                    "supercategory": "none"
                    }
                coco_dct["categories"].append(cat)
                cat_id_next += 1
            cat_id = [ cat["id"] for cat in coco_dct["categories"] if cat["name"] == bbox.class_name ][0]

            ann = {
                "id": ann_id_next,
                "image_id": image_id,
                "category_id": cat_id,
                "segmentation": [],
                "bbox": bbox.xywh,
                "area": bbox.area,
                "iscrowd": 0
                }
            coco_dct["annotations"].append(ann)
            ann_id_next += 1

    if os.path.dirname(fname_output_json) != "":
        os.makedirs(os.path.dirname(fname_output_json), exist_ok=True)
        logger.debug(f"Created directory {os.path.dirname(fname_output_json)}")
    with open(fname_output_json,'w') as f:        
        json.dump(coco_dct, f, indent=3)
        logger.debug(f"Wrote to {fname_output_json}")