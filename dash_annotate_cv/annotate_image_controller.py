from dash_annotate_cv.image_annotations import ImageAnnotations
from dash_annotate_cv.annotation_storage import AnnotationStorage, AnnotationWriter
from dash_annotate_cv.image_source import ImageSource, ImageIterator, IndexAboveError
from dash_annotate_cv.label_source import LabelSource
from dash_annotate_cv.helpers import UnknownError, Xyxy

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, Union
from PIL import Image
from mashumaro import DataClassDictMixin
import os
import datetime
import json
import random
from enum import Enum
import copy
import logging


logger = logging.getLogger(__name__)


@dataclass
class Bbox:
    xyxy: Xyxy
    class_name: Optional[str]
    is_highlighted: bool = False


    def __repr__(self):
        return f"Bbox(xyxy={[int(x) for x in self.xyxy]}, class_name={self.class_name})"


    def __eq__(self, other):
        if not isinstance(other, Bbox):
            return False
        return self.xyxy == other.xyxy and self.class_name == other.class_name


def bbox_eq_annotation(bbox: Bbox, bbox_ann: ImageAnnotations.Annotation.Bbox) -> bool:
    return bbox.xyxy == bbox_ann.xyxy and bbox.class_name == bbox_ann.class_name


class InvalidBboxError(Exception):
    pass


class NoUpdate(Enum):
    NO_UPDATE = "NO_UPDATE"


@dataclass
class BboxUpdate:
    idx: int
    xyxy_new: Union[NoUpdate,Xyxy] = NoUpdate.NO_UPDATE
    class_name_new: Union[NoUpdate,Optional[str]] = NoUpdate.NO_UPDATE


    def __repr__(self):
        return f"BboxUpdate(idx={self.idx}, xyxy_new={self.xyxy_new}, class_name_new={self.class_name_new})"


@dataclass
class ImageAnn:
    image_idx: int
    image_name: str
    image: Image.Image
    label_single: Optional[str]
    label_multiple: Optional[List[str]]
    bboxs: Optional[List[Bbox]]

    def __repr__(self):
        return f"ImageAnn(image_idx={self.image_idx}, image_name={self.image_name}, label_single={self.label_single}, label_multiple={self.label_multiple}, bboxs={self.bboxs})"


@dataclass
class AnnotateImageOptions(DataClassDictMixin):
    """Options
    """        

    # Instructions
    instructions_custom: Optional[str] = None

    # Whether to store timestamps
    store_timestamps: bool = True

    # Whether to store history
    store_history: bool = True

    # Whether to use the basename of the image for the annotation
    use_basename_for_image: bool = False

    # Name of author to store
    author: Optional[str] = None

    # Class to color
    class_to_color: Optional[Dict[str,Tuple[int,int,int]]] = None

    # Default color
    default_bbox_color: Tuple[int,int,int] = (64,64,88)

    def check_valid(self):
        """Check options are valid
        """        
        if self.class_to_color is not None:
            assert isinstance(self.class_to_color, dict), "class_to_color must be a dict"
            for k,v in self.class_to_color.items():
                assert isinstance(k,str), "class_to_color keys must be strings"
                assert isinstance(v,tuple), "class_to_color values must be tuples"
                assert len(v) == 3, "class_to_color values must be tuples of length 3"

    def _random_col(self) -> Tuple[int,int,int]:
        # Don't allow too bright or too dark colors = hard to see
        rgb = None
        while rgb is None or sum(rgb) > 675 or sum(rgb) < 100:
            rgb = (int(255*random.random()),int(255*random.random()),int(255*random.random()))
        return rgb

    def get_assign_color_for_class(self, class_name: str) -> Tuple[int,int,int]:
        """Get color for class, or assign a random color if not already assigned

        Args:
            class_name (str): Class name

        Returns:
            Tuple[int,int,int]: RGB color values (255 max)
        """        
        if self.class_to_color is None:
            self.class_to_color = {}
        if not class_name in self.class_to_color:
            # Random
            self.class_to_color[class_name] = self._random_col()
            logger.debug(f"Assigned color {self.class_to_color[class_name]} to class {class_name}")
        return self.class_to_color[class_name]


class NoCurrLabelError(Exception):
    """No current label
    """
    pass


class InvalidLabelError(Exception):
    """Invalid label
    """
    pass


class AnnotateImageController:
    """Image annotation controller
    """


    def __init__(
        self,
        label_source: LabelSource,
        image_source: ImageSource,
        annotation_storage: AnnotationStorage = AnnotationStorage(),
        annotations_existing: Optional[ImageAnnotations] = None,
        options: AnnotateImageOptions = AnnotateImageOptions()
        ):
        """Constructor

        Args:
            label_source (LabelSource): Source of labels
            image_source (ImageSource): Source of images
            annotation_storage (AnnotationStorage, optional): Where to store annotations. Defaults to AnnotationStorage().
            annotations_existing (Optional[ImageAnnotations], optional): Existing annotations to continue from, if any. Defaults to None.
            options (Options, optional): Options. Defaults to Options().
        """
        options.check_valid()
        self.options = options
        self.annotation_writer = AnnotationWriter(annotation_storage)
        self.label_source = label_source
        self.image_source = image_source
        self._labels = label_source.get_labels()
        self.annotations = annotations_existing or ImageAnnotations.new()
        self._image_iterator = ImageIterator(self.image_source)

        # Load the first image
        try:
            image_idx, image_name, image = self._image_iterator.next()
            self._update_curr(image_idx, image_name, image)
        except IndexAboveError:
            self._curr: Optional[ImageAnn] = None
    

    @property
    def no_images(self) -> int:
        """Number of images in dataset

        Returns:
            int: Number of images in dataset
        """        
        return self._image_iterator.no_images


    @property
    def labels(self) -> List[str]:
        """Labels

        Returns:
            List[str]: Labels
        """        
        return list(self._labels)


    @property
    def curr(self) -> Optional[ImageAnn]:
        """Current image,label to label

        Returns:
            Optional[ImageLabel]: Current image,label to label
        """        
        return self._curr


    @property
    def curr_bboxs(self) -> List[Bbox]:
        """Current bounding boxes

        Returns:
            List[Bbox]: List of bounding boxes
        """        
        if self.curr is None:
            return []
        return self.curr.bboxs or []


    @property
    def _curr_image_name(self) -> str:
        if self._curr is None:
            raise NoCurrLabelError("No current label")
        return os.path.basename(self._curr.image_name) if self.options.use_basename_for_image else self._curr.image_name


    @property
    def _timestamp_or_none(self) -> Optional[float]:
        return datetime.datetime.now().timestamp() if self.options.store_timestamps else None


    def add_bbox(self, bbox: Bbox):
        """Add bounding box

        Args:
            bbox (Bbox): Bounding box

        Raises:
            InvalidLabelError: Invalid label
        """        
        logger.debug(f"Adding bbox: {bbox}")

        # Store the annotation
        ann = self.annotations.get_or_add_image(self._curr_image_name, with_bboxs=True)

        # Check labels are allowed
        if bbox.class_name is not None and not bbox.class_name in self._labels:
            raise InvalidLabelError("Label value: %s not in allowed labels: %s" % (bbox.class_name, str(self._labels)))
        self._check_xyxy_valid(bbox.xyxy)

        # Add bounding box
        bbox_obj = ImageAnnotations.Annotation.Bbox(
            xyxy=bbox.xyxy,
            class_name=bbox.class_name,
            timestamp=self._timestamp_or_none,
            author=self.options.author
            )
        ann.bboxs = (ann.bboxs or []) + [bbox_obj]

        # History
        if self.options.store_history:
            op = ImageAnnotations.Annotation.BboxHistory(
                operation=ImageAnnotations.Annotation.BboxHistory.Operation.ADD,
                bbox=copy.deepcopy(bbox_obj)
                )
            ann.history_bboxs = [op] + (ann.history_bboxs or [])

        # Write
        self.annotation_writer.write(self.annotations)

        # Refresh
        self._refresh_curr()


    def delete_bbox(self, idx: int):
        """Delete bounding box

        Args:
            idx (int): Index of bounding box to delete

        Raises:
            UnknownError: Unknown error
        """        
        # Update annotation
        ann = self.annotations.get_or_add_image(self._curr_image_name, with_bboxs=True)
        if ann.bboxs is None:
            raise UnknownError("Bboxs must be set")
        if idx >= len(ann.bboxs):
            raise UnknownError("Bbox idx must be less than number of bboxs")
        bbox_old = ann.bboxs[idx]
        del ann.bboxs[idx]
        
        # History
        if self.options.store_history:
            op = ImageAnnotations.Annotation.BboxHistory(
                operation=ImageAnnotations.Annotation.BboxHistory.Operation.DELETE,
                bbox=copy.deepcopy(bbox_old)
                )
            ann.history_bboxs = [op] + (ann.history_bboxs or [])

        # Write
        self.annotation_writer.write(self.annotations)

        # Refresh
        self._refresh_curr()


    def update_bbox(self, update: BboxUpdate):
        """Update bounding box

        Args:
            update (BboxUpdate): Update

        Raises:
            UnknownError: Unknown error
            InvalidLabelError: Invalid label
            InvalidBboxError: Invalid bounding box
        """        
        # Store the annotation
        ann = self.annotations.get_or_add_image(self._curr_image_name, with_bboxs=True)

        # Update the bbox
        if ann.bboxs is None:
            raise UnknownError("Bboxs must be set")
        if update.xyxy_new != NoUpdate.NO_UPDATE:
            self._check_xyxy_valid(update.xyxy_new)
            ann.bboxs[update.idx].xyxy = update.xyxy_new
        if update.class_name_new != NoUpdate.NO_UPDATE:
            if not update.class_name_new in self._labels:
                raise InvalidLabelError("Label value: %s not in allowed labels: %s" % (update.class_name_new, str(self._labels)))
            ann.bboxs[update.idx].class_name = update.class_name_new
        
        # Update timestamp
        ann.bboxs[update.idx].timestamp = self._timestamp_or_none

        # History
        if self.options.store_history:
            op = ImageAnnotations.Annotation.BboxHistory(
                operation=ImageAnnotations.Annotation.BboxHistory.Operation.UPDATE,
                bbox=copy.deepcopy(ann.bboxs[update.idx])
                )
            ann.history_bboxs = [op] + (ann.history_bboxs or [])

        # Write
        self.annotation_writer.write(self.annotations)

        # Refresh
        self._refresh_curr()


    def store_label_multiple(self, label_values: List[str]):
        """Store multiple labels for image

        Args:
            label_values (List[str]): Label values

        Raises:
            NoCurrLabelError: If no current label
            InvalidLabelError: If provided label is not in label source
        """
        if type(label_values) != list:
            raise UnknownError("label_values must be a list")

        for label_value in label_values:
            if not label_value in self._labels:
                raise InvalidLabelError("Label value: %s not in allowed labels: %s" % (label_value, str(self._labels)))

        label = ImageAnnotations.Annotation.Label(
            multiple=label_values,
            timestamp=self._timestamp_or_none,
            author=self.options.author
            )
        self._store_label(label)
        
    def store_label_single(self, label_value: str):
        """Store label for image

        Args:
            label_value (str): Label value

        Raises:
            NoCurrLabelError: If no current label
            InvalidLabelError: If provided label is not in label source
        """

        if type(label_value) != str:
            raise UnknownError("label_value must be a string")

        if not label_value in self._labels:
            raise InvalidLabelError("Label value: %s not in allowed labels: %s" % (label_value, str(self._labels)))

        # Label
        label = ImageAnnotations.Annotation.Label(
            single=label_value,
            timestamp=self._timestamp_or_none,
            author=self.options.author
            )
        self._store_label(label)


    def next_image(self):
        """Skip to next image
        """        
        image_idx, image_name, image = self._image_iterator.next()
        self._update_curr(image_idx, image_name, image)


    def previous_image(self):
        """Go to previous image
        """        
        image_idx, image_name, image = self._image_iterator.prev()
        self._update_curr(image_idx, image_name, image)


    def skip_to_next_missing_ann(self):
        """Skip to next image with no annotation
        """        
        image, image_idx = None, None
        image_name = self._curr.image_name if self._curr is not None else None
        while image_name in self.annotations.image_to_entry:
            image_idx, image_name, image = self._image_iterator.next()
        if image is not None and image_idx is not None and image_name is not None:
            # Changed image
            self._update_curr(image_idx, image_name, image)
        else:
            self._curr = None


    def _refresh_curr(self):
        if self._curr is not None:
            logger.debug(f"Refreshing curr: {self.curr}")
            self._update_curr(self._curr.image_idx, self._curr.image_name, self._curr.image)
        else:
            logger.debug("No curr to refresh")


    def _update_curr(self, image_idx: int, image_name: str, image: Image.Image):
        label_single: Optional[str] = None  
        label_multiple: Optional[List[str]] = None
        bboxs: Optional[List[Bbox]] = None

        # Retrieve the label if it exists
        if image_name in self.annotations.image_to_entry:
            entry = self.annotations.image_to_entry[image_name]
            if entry.label is not None:
                label_single = entry.label.single
                label_multiple = entry.label.multiple
            if entry.bboxs is not None:
                bboxs = []
                for bbox in entry.bboxs:
                    bbox_obj = Bbox(
                        xyxy=bbox.xyxy,
                        class_name=bbox.class_name
                        )
                    bboxs.append(bbox_obj)
        
        self._curr = ImageAnn(image_idx, image_name, image, label_single, label_multiple, bboxs)
        logger.debug(f"Updated curr: {self._curr}")

    
    def _check_xyxy_valid(self, xyxy: Xyxy):
        if len(xyxy) != 4:
            raise InvalidBboxError("xyxy must have length 4")
        if xyxy[0] >= xyxy[2] or xyxy[1] >= xyxy[3]:
            raise InvalidBboxError("xyxy must be in format [x1,y1,x2,y2] where x1 < x2 and y1 < y2")


    def _store_label(self, label: ImageAnnotations.Annotation.Label):
        if self._curr is None:
            raise NoCurrLabelError("No current label")

        # Store the annotation
        image_name = os.path.basename(self._curr.image_name) if self.options.use_basename_for_image else self._curr.image_name

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
            ann.history_labels = [copy.deepcopy(label)] + (ann.history_labels or [])
        
        # Write
        self.annotation_writer.write(self.annotations)

        # Load the next image
        image_idx, image_name, image = self._image_iterator.next()
        self._update_curr(image_idx, image_name, image)


def load_image_anns_if_exist(storage: AnnotationStorage) -> Optional[ImageAnnotations]:
    """Load image annotations if they exist

    Args:
        storage (AnnotationStorage): Storage

    Raises:
        UnknownError: Unknown error

    Returns:
        Optional[ImageAnnotations]: Image annotations if they exist
    """    
    if storage.storage_type == AnnotationStorage.Type.NONE:
        return None
    elif storage.storage_type == AnnotationStorage.Type.JSON:
        if storage.json_file is None:
            raise UnknownError("json_file must be set if storage_type is JSON")

        # Restart from existing annotations if any
        if os.path.exists(storage.json_file):
            with open(storage.json_file,"r") as f:
                return ImageAnnotations.from_dict(json.load(f))
        else:
            return None