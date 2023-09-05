# Dash Annotate CV - A dash library for computer vision annotation tasks

`dash_annotate_cv` is a Python Dash library for computer vision annotation tasks.

Supported tasks:
* Annotation of images (whole image labels)

Roadmap for future tasks:
* Annotating multiple labels per image
* Annotating bounding boxes
* Annotating videos
* Annotating tags

**Note**: this library is not meant for production usage. It is meant to be used for quick prototyping and testing of annotation tasks.

## Example

You can also check out the [examples](examples).

```python
from dash import Dash, html
from dash_annotate_cv import AnnotateImageLabelsAIO, ImageSource, LabelSource, AnnotationStorage, ImageAnnotations
import dash_bootstrap_components as dbc
from skimage import data

# Load some images
images = [ ("chelsea",data.chelsea()), ("astronaut",data.astronaut()), ("camera",data.camera()) ]

# Set up the image and label sources
image_source = ImageSource(images=images)
label_source = LabelSource(labels=["astronaut", "camera", "cat"])

# Set up writing
storage = AnnotationStorage(storage_type=AnnotationStorage.Type.JSON, json_file="annotations.json")

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    html.H1("Annotate Images"),
    AnnotateImageLabelsAIO(label_source, image_source, annotation_storage=storage)
    ])
app.run(debug=True)
```