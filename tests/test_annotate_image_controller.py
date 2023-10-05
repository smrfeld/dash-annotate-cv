import dash_annotate_cv as dacv
from skimage import data
from PIL import Image
import pytest

@pytest.fixture
def controller():
    images = [ ("chelsea",data.chelsea()), ("astronaut",data.astronaut()), ("camera",data.camera()) ] # type: ignore
    images_pil = [ (name,Image.fromarray(image)) for name,image in images ]
    return dacv.AnnotateImageController(
        label_source=dacv.LabelSource(labels=["cat", "dog"]),
        image_source=dacv.ImageSource(images=images_pil),
        annotation_storage=dacv.AnnotationStorage(),
        options=dacv.AnnotateImageOptions()
        )

@pytest.fixture
def empty_controller():
    return dacv.AnnotateImageController(
        label_source=dacv.LabelSource(labels=["cat", "dog"]),
        image_source=dacv.ImageSource(images=[]),
        annotation_storage=dacv.AnnotationStorage(),
        options=dacv.AnnotateImageOptions()
        )

class TestAnnotateImageController:

    def test_add_bbox(self, controller: dacv.AnnotateImageController):
        # Init state
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"

        # Add bbox
        bbox = dacv.Bbox(xyxy=[0,0,10,10], class_name="cat")
        controller.add_bbox(bbox)

        # Check stored
        assert controller.annotations.image_to_entry["chelsea"].bboxs is not None
        assert len(controller.annotations.image_to_entry["chelsea"].bboxs) == 1
        assert dacv.bbox_eq_annotation(bbox, controller.annotations.image_to_entry["chelsea"].bboxs[0])

        # Check same image
        assert controller.curr is not None
        assert controller.curr.image_idx == 0
        assert controller.curr.image_name == "chelsea"

        # Check bboxs of curr
        assert controller.curr.bboxs is not None
        assert len(controller.curr.bboxs) == 1
        assert controller.curr.bboxs[0] == bbox

        # Advance
        controller.next_image()
        
        # Check next image
        assert controller.curr is not None
        assert controller.curr.image_idx == 1
        assert controller.curr.image_name == "astronaut"
        
        # Test adding invalid label
        with pytest.raises(dacv.InvalidLabelError):
            bbox = dacv.Bbox(xyxy=[0,0,10,10], class_name="zebra")
            controller.add_bbox(bbox)

        # Test adding invalid bbox
        # No negatives
        with pytest.raises(dacv.InvalidBboxError):
            bbox = dacv.Bbox(xyxy=[0,0,-10,10], class_name="cat")
            controller.add_bbox(bbox)
        # Must be 4 values
        with pytest.raises(dacv.InvalidBboxError):
            bbox = dacv.Bbox(xyxy=[0,10,10], class_name="cat")
            controller.add_bbox(bbox)

    def test_delete_bbox(self, controller: dacv.AnnotateImageController):
        # Init state
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"

        # Add bboxs
        bbox1 = dacv.Bbox(xyxy=[0,0,10,10], class_name="cat")
        controller.add_bbox(bbox1)
        bbox2 = dacv.Bbox(xyxy=[0,20,30,40], class_name="dog")
        controller.add_bbox(bbox2)

        # Check stored
        assert controller.annotations.image_to_entry["chelsea"].bboxs is not None
        assert len(controller.annotations.image_to_entry["chelsea"].bboxs) == 2
        assert dacv.bbox_eq_annotation(bbox1, controller.annotations.image_to_entry["chelsea"].bboxs[0])
        assert dacv.bbox_eq_annotation(bbox2, controller.annotations.image_to_entry["chelsea"].bboxs[1])

        # Delete bbox
        controller.delete_bbox(0)

        # Check stored
        assert controller.annotations.image_to_entry["chelsea"].bboxs is not None
        assert len(controller.annotations.image_to_entry["chelsea"].bboxs) == 1
        assert dacv.bbox_eq_annotation(bbox2, controller.annotations.image_to_entry["chelsea"].bboxs[0])

        # Check bboxs of curr
        assert controller.curr.bboxs is not None
        assert len(controller.curr.bboxs) == 1
        assert controller.curr.bboxs[0] == bbox2

    def test_update_bbox(self, controller: dacv.AnnotateImageController):
        # Init state
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"

        # Add bboxs
        bbox = dacv.Bbox(xyxy=[0,0,10,10], class_name="cat")
        controller.add_bbox(bbox)

        # Check curr
        assert len(controller.curr_bboxs) == 1
        assert controller.curr_bboxs[0] == bbox

        # Update bbox
        bbox_update = dacv.BboxUpdate(idx=0, xyxy_new=[0,0,20,20])
        controller.update_bbox(bbox_update)

        # Check stored
        assert controller.annotations.image_to_entry["chelsea"].bboxs is not None
        assert len(controller.annotations.image_to_entry["chelsea"].bboxs) == 1
        bbox_new = dacv.Bbox(xyxy=[0,0,20,20], class_name="cat")
        assert dacv.bbox_eq_annotation(bbox_new, controller.annotations.image_to_entry["chelsea"].bboxs[0])

        # Check curr
        assert len(controller.curr_bboxs) == 1
        assert controller.curr_bboxs[0] == bbox_new

        # Update again
        bbox_update = dacv.BboxUpdate(idx=0, class_name_new="dog")
        controller.update_bbox(bbox_update)

        # Check stored
        assert controller.annotations.image_to_entry["chelsea"].bboxs is not None
        assert len(controller.annotations.image_to_entry["chelsea"].bboxs) == 1
        bbox_new = dacv.Bbox(xyxy=[0,0,20,20], class_name="dog")
        assert dacv.bbox_eq_annotation(bbox_new, controller.annotations.image_to_entry["chelsea"].bboxs[0])

        # Check curr
        assert len(controller.curr_bboxs) == 1
        assert controller.curr_bboxs[0] == bbox_new


    def test_store_label(self, controller: dacv.AnnotateImageController):        
        # Init state
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"

        # Label
        controller.store_label_single("cat")

        # Check stored
        assert controller.annotations.image_to_entry["chelsea"].label is not None
        assert controller.annotations.image_to_entry["chelsea"].label.single == "cat"

        # Check next
        assert controller.curr is not None
        assert controller.curr.image_idx == 1
        assert controller.curr.image_name == "astronaut"

    def test_store_label_multiple(self, controller: dacv.AnnotateImageController):        
        # Init state
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"

        # Label
        controller.store_label_multiple(["cat","dog"])

        # Check stored
        assert controller.annotations.image_to_entry["chelsea"].label is not None
        assert controller.annotations.image_to_entry["chelsea"].label.multiple == ["cat","dog"]

        # Check next
        assert controller.curr is not None
        assert controller.curr.image_idx == 1
        assert controller.curr.image_name == "astronaut"

    def test_store_invalid_label(self, controller: dacv.AnnotateImageController):
        with pytest.raises(dacv.InvalidLabelError):
            controller.store_label_single("invalid")

    def test_store_no_curr(self, empty_controller: dacv.AnnotateImageController):
        with pytest.raises(dacv.NoCurrLabelError):
            empty_controller.store_label_single("cat")

    def test_next_image(self, controller: dacv.AnnotateImageController):
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.next_image()
        assert controller.curr is not None
        assert controller.curr.image_name == "astronaut"

    def test_previous_image(self, controller: dacv.AnnotateImageController):
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.next_image()
        controller.previous_image()
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"

    def test_skip_to_next_missing_ann(self, controller: dacv.AnnotateImageController):
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.store_label_single("cat")
        assert controller.curr is not None
        assert controller.curr.image_name == "astronaut"
        controller.store_label_single("dog")
        assert controller.curr is not None
        assert controller.curr.image_name == "camera"
        controller.previous_image()
        controller.previous_image()
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.skip_to_next_missing_ann()
        assert controller.curr is not None
        assert controller.curr.image_name == "camera"


