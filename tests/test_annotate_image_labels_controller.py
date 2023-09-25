from dash_annotate_cv import AnnotateImageController, AnnotateImageOptions, ImageSource, LabelSource, AnnotationStorage, InvalidLabelError, NoCurrLabelError
from skimage import data
import pytest

@pytest.fixture
def controller():
    images = [ ("chelsea",data.chelsea()), ("astronaut",data.astronaut()), ("camera",data.camera()) ] # type: ignore
    return AnnotateImageController(
        label_source=LabelSource(labels=["cat", "dog"]),
        image_source=ImageSource(images=images),
        annotation_storage=AnnotationStorage(),
        options=AnnotateImageOptions()
        )

@pytest.fixture
def empty_controller():
    return AnnotateImageController(
        label_source=LabelSource(labels=["cat", "dog"]),
        image_source=ImageSource(images=[]),
        annotation_storage=AnnotationStorage(),
        options=AnnotateImageOptions()
        )

class TestAnnotateImageLabelsController:

    def test_store_label(self, controller: AnnotateImageController):        
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

    def test_store_label_multiple(self, controller: AnnotateImageController):        
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

    def test_store_invalid_label(self, controller: AnnotateImageController):
        with pytest.raises(InvalidLabelError):
            controller.store_label_single("invalid")

    def test_store_no_curr(self, empty_controller: AnnotateImageController):
        with pytest.raises(NoCurrLabelError):
            empty_controller.store_label_single("cat")

    def test_skip(self, controller: AnnotateImageController):
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.next_image()
        assert controller.curr is not None
        assert controller.curr.image_name == "astronaut"

    def test_previous(self, controller: AnnotateImageController):
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.next_image()
        controller.previous_image()
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"

    def test_skip_to_next_missing_ann(self, controller: AnnotateImageController):
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


