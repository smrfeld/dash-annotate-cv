from dash import Dash, html
from dash_annotate import AnnotateImageLabelsAIO, ImageSource, LabelSource, AnnotationStorage
import dash_bootstrap_components as dbc
from skimage import data

if __name__ == "__main__":

    # Load some images
    images = [ ("chelsea",data.chelsea()), ("astronaut",data.astronaut()), ("camera",data.camera()) ]

    # Set up the image and label sources
    image_source = ImageSource(images=images)
    label_source = LabelSource(labels=["astronaut", "camera", "cat"])

    # Set up writing
    storage = AnnotationStorage(storage_type=AnnotationStorage.Type.JSON, json_file="annotations.json")

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = html.Div([
        html.H1("Annotate Images"),
        AnnotateImageLabelsAIO(label_source, image_source, annotation_storage=storage)
        ])
    app.run(debug=True)