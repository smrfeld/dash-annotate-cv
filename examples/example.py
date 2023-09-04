from dash import Dash
from dash_annotate import AnnotateImageLabelsAIO, ImageSource, LabelSource
from skimage import data

if __name__ == "__main__":

    img = data.chelsea() # type: ignore

    image_source = ImageSource(images=[img])
    label_source = LabelSource(labels=["cat", "dog", "bird"])

    app = Dash(__name__)
    app.layout = AnnotateImageLabelsAIO(label_source, image_source)

    app.run(debug=True)