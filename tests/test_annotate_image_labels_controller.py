from dash_annotate_cv import AnnotateImageLabelsController, AnnotateImageLabelsOptions, ImageAnnotations, ImageSource, LabelSource, AnnotationStorage, ImageLabel, InvalidLabelError, NoCurrLabelError
from skimage import data
import pytest

@pytest.fixture
def controller():
    images = [ ("chelsea",data.chelsea()), ("astronaut",data.astronaut()), ("camera",data.camera()) ] # type: ignore
    return AnnotateImageLabelsController(
        label_source=LabelSource(labels=["cat", "dog"]),
        image_source=ImageSource(images=images),
        annotation_storage=AnnotationStorage(),
        options=AnnotateImageLabelsOptions()
        )

@pytest.fixture
def empty_controller():
    return AnnotateImageLabelsController(
        label_source=LabelSource(labels=["cat", "dog"]),
        image_source=ImageSource(images=[]),
        annotation_storage=AnnotationStorage(),
        options=AnnotateImageLabelsOptions()
        )

class TestAnnotateImageLabelsController:

    def test_store_label(self, controller: AnnotateImageLabelsController):        
        # Init state
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"

        # Label
        controller.store_label("cat")

        # Check stored
        assert controller.annotations.image_to_entry["chelsea"].label.single == "cat"

        # Check next
        assert controller.curr is not None
        assert controller.curr.image_idx == 1
        assert controller.curr.image_name == "astronaut"
    
    def test_store_invalid_label(self, controller: AnnotateImageLabelsController):
        with pytest.raises(InvalidLabelError):
            controller.store_label("invalid")

    def test_store_no_curr(self, empty_controller: AnnotateImageLabelsController):
        with pytest.raises(NoCurrLabelError):
            empty_controller.store_label("cat")

    def test_skip(self, controller: AnnotateImageLabelsController):
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.skip()
        assert controller.curr is not None
        assert controller.curr.image_name == "astronaut"

    def test_previous(self, controller: AnnotateImageLabelsController):
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.skip()
        controller.previous()
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"

    def test_skip_to_next_missing_ann(self, controller: AnnotateImageLabelsController):
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.store_label("cat")
        assert controller.curr is not None
        assert controller.curr.image_name == "astronaut"
        controller.store_label("dog")
        assert controller.curr is not None
        assert controller.curr.image_name == "camera"
        controller.previous()
        controller.previous()
        assert controller.curr is not None
        assert controller.curr.image_name == "chelsea"
        controller.skip_to_next_missing_ann()
        assert controller.curr is not None
        assert controller.curr.image_name == "camera"


