from dash_annotate_cv.image_annotations import ImageAnnotations
from dash_annotate_cv.annotation_storage import AnnotationStorage, AnnotationWriter
from dash_annotate_cv.image_source import ImageSource, ImageIterator
from dash_annotate_cv.label_source import LabelSource

from dataclasses import dataclass
from typing import Optional, List
from PIL import Image
from enum import Enum
from mashumaro import DataClassDictMixin
import os
import datetime
from collections import namedtuple

ImageLabel = namedtuple("ImageLabel", ["image_idx", "image_name", "image", "label_value"])

@dataclass
class ImageAnnotationOptions(DataClassDictMixin):
    """Options
    """        

    class SelectionMode(Enum):
        SINGLE = "single"
        MULTIPLE = "multiple"

    # Selection mode - how many labels can be selected at once
    selection_mode: SelectionMode = SelectionMode.SINGLE

    # Whether to store timestamps
    store_timestamps: bool = True

    # Whether to store history
    store_history: bool = True

    # Whether to use the basename of the image for the annotation
    use_basename_for_image: bool = False

    # Name of author to store
    author: Optional[str] = None

class ImageAnnotationController:

    def __init__(
        self,
        label_source: LabelSource,
        image_source: ImageSource,
        annotation_storage: AnnotationStorage = AnnotationStorage(),
        annotations_existing: Optional[ImageAnnotations] = None,
        options: ImageAnnotationOptions = ImageAnnotationOptions()
        ):
        self.options = options
        self.annotation_writer = AnnotationWriter(annotation_storage)
        self.label_source = label_source
        self.image_source = image_source
        self._labels = label_source.get_labels()
        self.annotations = annotations_existing or ImageAnnotations(image_to_entry={})
        self._image_iterator = ImageIterator(self.image_source)
        self._curr_image_label: Optional[ImageLabel] = None
    
    @property
    def no_images(self) -> int:
        return self._image_iterator.no_images

    @property
    def labels(self) -> List[str]:
        return list(self._labels)

    @property
    def curr_image_label(self) -> Optional[ImageLabel]:
        return self._curr_image_label

    def store_label(self, label_value: Optional[str]):

        if self._curr_image_label is not None and label_value is not None and label_value in self._labels:
                
            # Store the annotation
            image_name = os.path.basename(self._curr_image_label.image_name) if self.options.use_basename_for_image else self._curr_image_label.image_name

            # Label
            label = ImageAnnotations.Annotation.Label(
                single=label_value,
                timestamp=datetime.datetime.now().timestamp() if self.options.store_timestamps else None,
                author=self.options.author
                )

            did_update = False
            if image_name in self.annotations.image_to_entry:
                ann = self.annotations.image_to_entry[image_name]
                if ann.label != label:
                    ann.label = label
                    did_update = True
            else:
                ann = ImageAnnotations.Annotation(
                    image_name=image_name,
                    label=label
                    )
                self.annotations.image_to_entry[image_name] = ann
                did_update = True

            # Also add history
            if did_update and self.options.store_history:
                if ann.history is None:
                    ann.history = []
                ann.history.append(label)

            # Write
            self.annotation_writer.write(self.annotations)

        # Load the next image
        image_idx, image_name, image = self._image_iterator.next()
        label_value = self._get_existing_label_of_curr_image()
        self._curr_image_label = ImageLabel(image_idx, image_name, image, label_value)

    def skip(self):
        image_idx, image_name, image = self._image_iterator.next()
        label_value = self._get_existing_label_of_curr_image()
        self._curr_image_label = ImageLabel(image_idx, image_name, image, label_value)

    def previous(self):
        image_idx, image_name, image = self._image_iterator.prev()
        label_value = self._get_existing_label_of_curr_image()
        self._curr_image_label = ImageLabel(image_idx, image_name, image, label_value)

    def skip_to_next_missing_ann(self) -> Optional[ImageLabel]:
        image, image_idx = None, None
        image_name = self._curr_image_label.image_name if self._curr_image_label is not None else None
        while image_name in self.annotations.image_to_entry:
            image_idx, image_name, image = self._image_iterator.next()
        if image is not None and image_idx is not None and image_name is not None:
            # Changed image
            label_value = self._get_existing_label_of_curr_image()
            return ImageLabel(image_idx, image_name, image, label_value)
        return None

    def _get_existing_label_of_curr_image(self) -> Optional[str]:
        if self._curr_image_label is None:
            return None
        image_name = self._curr_image_label.image_name
        if image_name in self.annotations.image_to_entry:
            entry = self.annotations.image_to_entry[image_name]
            if entry.label.single is not None and entry.label.single in self._labels:
                return entry.label.single
        return None
