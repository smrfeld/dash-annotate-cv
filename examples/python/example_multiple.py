# Import dash_annotate_cv package
import dash_annotate_cv as dacv


# Other imports
from dash import Dash, html
import dash_bootstrap_components as dbc
from skimage import data
import logging
import sys
from PIL import Image


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
    images_pil = [ (name,Image.fromarray(image)) for name,image in images ]

    # Set up the image and label sources
    image_source = dacv.ImageSource(images=images_pil)
    label_source = dacv.LabelSource(labels=["astronaut", "camera", "cat", "cute", "photography", "space"])

    # Set up writing
    storage = dacv.AnnotationStorage(storage_types=[dacv.StorageType.JSON], json_file="example_multiple.json")
    annotations_existing = dacv.load_image_anns_from_storage(storage)
    
    aio = dacv.AnnotateImageLabelsAIO(
        label_source=label_source, 
        image_source=image_source, 
        annotation_storage=storage, 
        annotations_existing=annotations_existing, 
        options=dacv.AnnotateImageOptions(),
        selection_mode=dacv.SelectionMode.MULTIPLE
        )
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = dbc.Container([
        html.H1("Annotate Images"),
        aio
        ])
    app.run(debug=False)