from dash_annotate_cv.annotate_image_controller import AnnotateImageController, AnnotateImageOptions, ImageAnn, NoCurrLabelError, InvalidLabelError, load_image_anns_if_exist
from dash_annotate_cv.helpers import get_trigger_id
from dash_annotate_cv.image_source import ImageSource, IndexAboveError, IndexBelowError
from dash_annotate_cv.label_source import LabelSource
from dash_annotate_cv.image_annotations import ImageAnnotations
from dash_annotate_cv.annotation_storage import AnnotationStorage

from typing import Optional
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, no_update, callback
from skimage import data
import json
from dash import Output, Input, html, dcc, callback, MATCH
import uuid
from typing import Optional, Union, List
import plotly.express as px
import dash_bootstrap_components as dbc
from PIL import Image
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


class AnnotateImageBboxsAIO(html.Div):
    """Annotation component for images
    """

    # A set of functions that create pattern-matching callbacks of the subcomponents
    class ids:
        description = lambda aio_id: {
            'component': 'AnnotateImageBboxsAIO',
            'subcomponent': 'description',
            'aio_id': aio_id
        }
        image = lambda aio_id: {
            'component': 'AnnotateImageBboxsAIO',
            'subcomponent': 'image',
            'aio_id': aio_id
        }
        graph_picture = lambda aio_id: {
            'component': 'AnnotateImageBboxsAIO',
            'subcomponent': 'graph_picture',
            'aio_id': aio_id
        }

    ids = ids

    def __init__(self,
        label_source: LabelSource,
        image_source: ImageSource,
        annotation_storage: AnnotationStorage = AnnotationStorage(),
        annotations_existing: Optional[ImageAnnotations] = None,
        aio_id: Optional[str] = None,
        options: AnnotateImageOptions = AnnotateImageOptions()
        ):

        self.controller = AnnotateImageController(
            label_source=label_source,
            image_source=image_source,
            annotation_storage=annotation_storage,
            annotations_existing=annotations_existing,
            options=options
            )
        self._curr_image_layout = None

        # Allow developers to pass in their own `aio_id` if they're
        # binding their own callback to a particular component.
        if aio_id is None:
            # Otherwise use a uuid that has virtually no chance of collision.
            # Uuids are safe in dash deployments with processes
            # because this component's callbacks
            # use a stateless pattern-matching callback:
            # The actual ID does not matter as long as its unique and matches
            # the PMC `MATCH` pattern..
            self.aio_id = str(uuid.uuid4())
        else:
            self.aio_id = aio_id

        super().__init__(self._create_layout(self.aio_id)) # Equivalent to `html.Div([...])`
        self._define_callbacks()

    def _create_layout(self, aio_id: str):
        """Create layout for component
        """        
        logger.debug("Creating layout for component")

        self._curr_image_layout = self._create_layout_for_curr_image()  

        return dbc.Row([
            dbc.Col([
                html.Div(self._curr_image_layout, id=self.ids.image(aio_id))
            ], md=6),
            dbc.Col([
            ], md=6, id=self.ids.description(aio_id))
        ])

    def _create_layout_for_curr_image(self):
        """Create layout for the image
        """        
        image = self.controller.curr.image if self.controller.curr is not None else None
        if image is None:
            return []
        fig = px.imshow(image)
        fig.update_layout(dragmode="drawrect")
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        return dcc.Graph(id=self.ids.graph_picture(self.aio_id), figure=fig)
    
    def _define_callbacks(self):
        """Define callbacks
        """        
        logger.debug("Defining callbacks")
        @callback(
            Output(self.ids.description(MATCH), 'children'),
            Input(self.ids.graph_picture(MATCH), "relayoutData")
            )
        def update_bboxs(relayout_data):
            logger.debug("Updating bboxs")

            if "shapes" in relayout_data:
                return json.dumps(relayout_data["shapes"], indent=2)
            else:
                return no_update
        
        logger.debug("Defined callbacks")