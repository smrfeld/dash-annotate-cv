import dash_annotate_cv as dacv
import pytest
import os


@pytest.fixture(scope="session")
def storage_coco():
    # Clean up
    if os.path.exists("tmp_coco.json"):
        os.remove("tmp_coco.json")
    
    yield dacv.AnnotationStorage(
        storage_types=[dacv.StorageType.COCO],
        coco_file="tmp_coco.json"
        )

    # Clean up
    if os.path.exists("tmp_coco.json"):
        os.remove("tmp_coco.json")


@pytest.fixture(scope="session")
def storage_json():
    # Clean up
    if os.path.exists("tmp_json.json"):
        os.remove("tmp_json.json")
    
    yield dacv.AnnotationStorage(
        storage_types=[dacv.StorageType.JSON],
        json_file="tmp_json.json"
        )

    # Clean up
    if os.path.exists("tmp_json.json"):
        os.remove("tmp_json.json")


@pytest.fixture
def anns():
    return dacv.ImageAnnotations(
        image_to_entry={
            "test.jpg": dacv.ImageAnnotations.Annotation(
                image_name="test.jpg",
                label=dacv.ImageAnnotations.Annotation.Label(single="cat"),
                bboxs=[dacv.ImageAnnotations.Annotation.Bbox(xyxy=[1,2,3,4], class_name="cat")],
                image_height=100,
                image_width=100
                )
            }
        )


def anns_eq_by_bboxs(ann1: dacv.ImageAnnotations.Annotation, ann2: dacv.ImageAnnotations.Annotation):
    return ann1.image_name == ann2.image_name and \
        ann1.bboxs == ann2.bboxs and \
        ann1.image_height == ann2.image_height and \
        ann1.image_width == ann2.image_width


def image_anns_eq_by_bboxs(anns1: dacv.ImageAnnotations, anns2: dacv.ImageAnnotations):
    for image_name, ann in anns1.image_to_entry.items():
        if image_name not in anns2.image_to_entry:
            return False
        ann2 = anns2.image_to_entry[image_name]
        if not anns_eq_by_bboxs(ann, ann2):
            return False
    return True


class TestFormats:


    def test_coco(self, storage_coco: dacv.AnnotationStorage, anns: dacv.ImageAnnotations):
        writer = dacv.AnnotationWriter(storage_coco)
        writer.write(anns)
        assert storage_coco.coco_file is not None
        assert os.path.exists(storage_coco.coco_file)

        # Load
        # In COCO format, only bboxs are stored => special equality check
        anns_loaded = dacv.load_image_anns_from_storage(storage_coco)
        assert anns_loaded is not None
        image_anns_eq_by_bboxs(anns, anns_loaded)
    

    def test_json(self, storage_json: dacv.AnnotationStorage, anns: dacv.ImageAnnotations):
        writer = dacv.AnnotationWriter(storage_json)
        writer.write(anns)
        assert storage_json.json_file is not None
        assert os.path.exists(storage_json.json_file)

        # Load
        anns_loaded = dacv.load_image_anns_from_storage(storage_json)
        assert anns_loaded is not None
        assert anns == anns_loaded