# Import library
import dash_annotate_cv as dacv

# Other imports
from dash import Dash, html
import dash_bootstrap_components as dbc
import logging
import sys
import argparse
from dataclasses import dataclass, field
from mashumaro import DataClassDictMixin
import yaml
from enum import Enum


# Set up logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


@dataclass
class Conf(DataClassDictMixin):
    """Config file format for the command line utility

    Args:
        mode (Mode): Mode
        labels (dacv.LabelSource): Label source
        images (dacv.ImageSource): Image source
        storage (dacv.AnnotationStorage): Annotation storage
        options_image_labels (dacv.AnnotateImageLabelsOptions): Options for the image labels annotation
    """    

    class Mode(Enum):
        IMAGE_LABELS = "image_labels"

    
    mode: Mode
    label_source: dacv.LabelSource
    image_source: dacv.ImageSource
    storage: dacv.AnnotationStorage = field(default_factory=dacv.AnnotationStorage)
    options_image_labels: dacv.AnnotateImageLabelsOptions = field(default_factory=dacv.AnnotateImageLabelsOptions)


    def check_valid(self):
        pass


def cli():

    parser = argparse.ArgumentParser(description="Command line utility to launch a simple dash app to annotate images")
    parser.add_argument("conf", type=str, help="Path to the configuration file YAML file. See docs for details on the format.")
    args = parser.parse_args()

    # Load conf
    with open(args.conf,"r") as f:
        conf = Conf.from_dict(yaml.safe_load(f))
        conf.check_valid()

    # Restart from existing annotations if any
    annotations_existing = dacv.load_image_anns_if_exist(conf.storage)

    # Dash app
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    if conf.mode == Conf.Mode.IMAGE_LABELS:
        aio = dacv.AnnotateImageLabelsAIO(
            label_source=conf.label_source, 
            image_source=conf.image_source, 
            annotation_storage=conf.storage, 
            annotations_existing=annotations_existing, 
            options=conf.options_image_labels
            )
        app.layout = dbc.Container([
            html.H1("Annotate Images"),
            aio
            ])
    else:
        raise NotImplementedError(f"Unrecognized mode: '{conf.mode}'.")
        
    app.run(debug=False)