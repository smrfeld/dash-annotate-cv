from dash import Dash, html
from dash_annotate_cv import AnnotateImageLabelsAIO, ImageSource, LabelSource, AnnotationStorage, ImageAnnotations, AnnotateImageLabelsOptions
import dash_bootstrap_components as dbc
from skimage import data
import json
import os

if __name__ == "__main__":

    # Load some images
    images = [ ("chelsea",data.chelsea()), ("astronaut",data.astronaut()), ("camera",data.camera()) ] # type: ignore

    # Set up the image and label sources
    image_source = ImageSource(images=images)
    label_source = LabelSource(labels=["astronaut", "camera", "cat"])

    # Set up writing
    storage = AnnotationStorage(storage_type=AnnotationStorage.Type.JSON, json_file="example_single.json")

    # Restart from existing annotations if any
    if os.path.exists("example_single.json"):
        with open("example_single.json","r") as f:
            annotations_existing = ImageAnnotations.from_dict(json.load(f))
    else:
        annotations_existing = None
    
    # Options for the  - single or multi-selection
    options = AnnotateImageLabelsOptions(
        selection_mode=AnnotateImageLabelsOptions.SelectionMode.SINGLE
        )

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = dbc.Container([
        html.H1("Annotate Images"),
        AnnotateImageLabelsAIO(label_source, image_source, annotation_storage=storage, annotations_existing=annotations_existing, options=options)
        ])
    app.run(debug=False)