from dash_annotate_cv.image_annotations import ImageAnnotations
from dash_annotate_cv.annotation_storage import AnnotationStorage, AnnotationWriter
from dash_annotate_cv.image_source import ImageSource, ImageIterator, IndexAboveError
from dash_annotate_cv.label_source import LabelSource

from dataclasses import dataclass
from typing import Optional, List
from PIL import Image
from mashumaro import DataClassDictMixin
import os
import datetime
import json


@dataclass
class Bbox:
    xyxy: List[float]
    class_name: Optional[str]


@dataclass
class ImageAnn:
    image_idx: int
    image_name: str
    image: Image.Image
    label_single: Optional[str]
    label_multiple: Optional[List[str]]
    bboxs: Optional[List[Bbox]]


@dataclass
class AnnotateImageOptions(DataClassDictMixin):
    """Options
    """        

    # Whether to store timestamps
    store_timestamps: bool = True

    # Whether to store history
    store_history: bool = True

    # Whether to use the basename of the image for the annotation
    use_basename_for_image: bool = False

    # Name of author to store
    author: Optional[str] = None



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


    def store_bbox(self, bbox: Bbox):

        # Check label is allowed
        if bbox.class_name is not None:
            if not bbox.class_name in self._labels:
                raise InvalidLabelError("Label value: %s not in allowed labels: %s" % (bbox.class_name, str(self._labels)))

        # Bounding box
        bbox_obj = ImageAnnotations.Annotation.Bbox(
            xyxy=bbox.xyxy,
            class_name=bbox.class_name,
            timestamp=datetime.datetime.now().timestamp() if self.options.store_timestamps else None,
            author=self.options.author
            )

        if self._curr is None:
            raise NoCurrLabelError("No current label")

        # Store the annotation
        image_name = os.path.basename(self._curr.image_name) if self.options.use_basename_for_image else self._curr.image_name
        if image_name in self.annotations.image_to_entry:
            ann = self.annotations.image_to_entry[image_name]
            if ann.bboxs is None:
                ann.bboxs = []
            ann.bboxs.append(bbox_obj)
        else:
            ann = ImageAnnotations.Annotation(
                image_name=image_name,
                bboxs=[ bbox_obj ]
                )

        # Also add history
        if self.options.store_history:
            if ann.history is None:
                ann.history = []
            ann.history.append(bbox_obj)

        # Write
        self.annotation_writer.write(self.annotations)


    def store_label_multiple(self, label_values: List[str]):
        """Store multiple labels for image

        Args:
            label_values (List[str]): Label values

        Raises:
            NoCurrLabelError: If no current label
            InvalidLabelError: If provided label is not in label source
        """

        for label_value in label_values:
            if not label_value in self._labels:
                raise InvalidLabelError("Label value: %s not in allowed labels: %s" % (label_value, str(self._labels)))

        label = ImageAnnotations.Annotation.Label(
            multiple=label_values,
            timestamp=datetime.datetime.now().timestamp() if self.options.store_timestamps else None,
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

        if not label_value in self._labels:
            raise InvalidLabelError("Label value: %s not in allowed labels: %s" % (label_value, str(self._labels)))

        # Label
        label = ImageAnnotations.Annotation.Label(
            single=label_value,
            timestamp=datetime.datetime.now().timestamp() if self.options.store_timestamps else None,
            author=self.options.author
            )
        self._store_label(label)


    def _store_label(self, label: ImageAnnotations.Annotation.Label):
        """Store label for image

        Args:
            label_value (str): Label value

        Raises:
            NoCurrLabelError: If no current label
            InvalidLabelError: If provided label is not in label source
        """        
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
            if ann.history is None:
                ann.history = []
            ann.history.append(label)

        # Write
        self.annotation_writer.write(self.annotations)

        # Load the next image
        image_idx, image_name, image = self._image_iterator.next()
        self._update_curr(image_idx, image_name, image)


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


    def _update_curr(self, image_idx: int, image_name: str, image: Image.Image) :
        """Get existing label for image

        Args:
            image_name (str): Name of image
        """      
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


def load_image_anns_if_exist(storage: AnnotationStorage) -> Optional[ImageAnnotations]:
    if storage.storage_type == AnnotationStorage.Type.NONE:
        return None
    elif storage.storage_type == AnnotationStorage.Type.JSON:
        assert storage.json_file is not None, "json_file must be set if storage_type is JSON"

        # Restart from existing annotations if any
        if os.path.exists(storage.json_file):
            with open(storage.json_file,"r") as f:
                return ImageAnnotations.from_dict(json.load(f))
        else:
            return None