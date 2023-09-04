from dash import Dash
from dash_annotate import AnnotateImageLabelsAIO, ImageSource, LabelSource
import dash_bootstrap_components as dbc
from skimage import data

if __name__ == "__main__":

    # Load some images
    images = [ data.chelsea(), data.astronaut(), data.camera() ] # type: ignore

    # Set up the image and label sources
    image_source = ImageSource(images=images)
    label_source = LabelSource(labels=["cat", "dog", "bird"])

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = AnnotateImageLabelsAIO(label_source, image_source)

    app.run(debug=True)