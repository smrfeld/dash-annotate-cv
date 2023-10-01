import dash_annotate_cv as dacv
import pytest
from typing import Dict, List

@pytest.fixture
def converter():
    return dacv.BboxToShapeConverter(options=dacv.AnnotateImageOptions(
        class_to_color={
            "cat": (0,255,0),
            "dog": (0,0,255)
        }
    ))

@pytest.fixture
def figure():
    return {
        'layout': {
            'shapes': []
        }
    }

@pytest.fixture
def matching_bboxs():
    return [
        dacv.Bbox(xyxy=[0,0,10,10], class_name="cat"),
        dacv.Bbox(xyxy=[10,10,20,20], class_name="dog")
        ]

@pytest.fixture
def matching_shapes():
    return [
        {
            'x0': 0,
            'y0': 0,
            'x1': 10,
            'y1': 10,
            'line': {'color': 'rgba(0,255,0,1)'}
        },
        {
            'x0': 10,
            'y0': 10,
            'x1': 20,
            'y1': 20,
            'line': {'color': 'rgba(0,0,255,1)'}
        }
        ]

def check_shapes_match(shapes: List[Dict], shapes_match: List[Dict]):
    assert len(shapes) == len(shapes_match)
    for i in range(len(shapes)):
        shape = shapes[i]
        shape_match = shapes_match[i]
        assert shape['x0'] == shape_match['x0']
        assert shape['y0'] == shape_match['y0']
        assert shape['x1'] == shape_match['x1']
        assert shape['y1'] == shape_match['y1']
        assert shape['line']['color'] == shape_match['line']['color']

class TestBboxToShapeConverter:

    def test_refresh_figure_shapes(self, figure: Dict, converter: dacv.BboxToShapeConverter, matching_bboxs: List[dacv.Bbox], matching_shapes: List[Dict]):
        assert len(figure['layout']['shapes']) == 0
        converter.refresh_figure_shapes(figure, matching_bboxs)
        check_shapes_match(figure['layout']['shapes'], matching_shapes)

    def test_shape_to_bbox(self, converter: dacv.BboxToShapeConverter, matching_shapes: List[Dict], matching_bboxs: List[dacv.Bbox]):
        bbox = converter.shape_to_bbox(matching_shapes[0])
        assert bbox.xyxy == matching_bboxs[0].xyxy
        assert bbox.class_name is None

    def test_bboxs_to_shapes(self, converter: dacv.BboxToShapeConverter, matching_bboxs: List[dacv.Bbox], matching_shapes: List[Dict]):
        shapes = converter.bboxs_to_shapes(matching_bboxs)
        check_shapes_match(shapes, matching_shapes)
    
    def test_bbox_to_shape(self, converter: dacv.BboxToShapeConverter, matching_bboxs: List[dacv.Bbox], matching_shapes: List[Dict]):
        shape = converter.bbox_to_shape(matching_bboxs[0])
        check_shapes_match([shape], [matching_shapes[0]])