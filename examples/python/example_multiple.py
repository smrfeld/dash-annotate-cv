# Import dash_annotate_cv package
import dash_annotate_cv as dacv


# Other imports
from dash import Dash, html
import dash_bootstrap_components as dbc
from skimage import data
import json
import os
import logging
import sys


# Set up logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


if __name__ == "__main__":

    # Load some images
    images = [ ("chelsea",data.chelsea()), ("astronaut",data.astronaut()), ("camera",data.camera()) ] # type: ignore

    # Set up the image and label sources
    image_source = dacv.ImageSource(images=images)
    label_source = dacv.LabelSource(labels=["astronaut", "camera", "cat", "cute", "photography", "space"])

    # Set up writing
    storage = dacv.AnnotationStorage(storage_type=dacv.AnnotationStorage.Type.JSON, json_file="example_multiple.json")
    annotations_existing = dacv.load_image_anns_if_exist(storage)
    
    # Options for the  - single or multi-selection
    options = dacv.AnnotateImageOptions(
        selection_mode=dacv.AnnotateImageOptions.SelectionMode.MULTIPLE
        )

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = dbc.Container([
        html.H1("Annotate Images"),
        dacv.AnnotateImageLabelsAIO(label_source, image_source, annotation_storage=storage, annotations_existing=annotations_existing, options=options)
        ])
    app.run(debug=False)