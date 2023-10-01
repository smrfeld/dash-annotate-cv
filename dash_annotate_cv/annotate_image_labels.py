from dash_annotate_cv.annotate_image_controller import AnnotateImageController, AnnotateImageOptions
from dash_annotate_cv.annotate_image_controls import AnnotateImageControlsAIO
from dash_annotate_cv.helpers import get_trigger_id
from dash_annotate_cv.image_source import ImageSource
from dash_annotate_cv.label_source import LabelSource
from dash_annotate_cv.image_annotations import ImageAnnotations
from dash_annotate_cv.annotation_storage import AnnotationStorage

from dash import Output, Input, html, dcc, callback, MATCH, no_update
from typing import Optional
import plotly.express as px
import dash_bootstrap_components as dbc
import logging
from enum import Enum


logger = logging.getLogger(__name__)


class SelectionMode(Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"


class AnnotateImageLabelsAIO(html.Div):
    """Annotation component for images
    """

    # A set of functions that create pattern-matching callbacks of the subcomponents
    class ids:
        dropdown = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'dropdown',
            'aio_id': aio_id
        }
        image = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'image',
            'aio_id': aio_id
        }
        alert_label = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'alert_label',
            'aio_id': aio_id
        }

    ids = ids

    def __init__(
        self,
        label_source: LabelSource,
        image_source: ImageSource,
        annotation_storage: AnnotationStorage = AnnotationStorage(),
        annotations_existing: Optional[ImageAnnotations] = None,
        aio_id: Optional[str] = None,
        options: AnnotateImageOptions = AnnotateImageOptions(),
        selection_mode: SelectionMode = SelectionMode.SINGLE
        ):
        """Constructor

        Args:
            label_source (LabelSource): Source of labels
            image_source (ImageSource): Source of images
            annotation_storage (AnnotationStorage, optional): Where to store annotations. Defaults to AnnotationStorage().
            annotations_existing (Optional[ImageAnnotations], optional): Existing annotations to continue from, if any. Defaults to None.
            aio_id (Optional[str], optional): IDs for components. Defaults to None.
            options (Options, optional): Options. Defaults to Options().
            selection_mode (SelectionMode): Selection mode. Defaults to SelectionMode.SINGLE.
        """
        self.controller = AnnotateImageController(
            label_source=label_source,
            image_source=image_source,
            annotation_storage=annotation_storage,
            annotations_existing=annotations_existing,
            options=options
            )
        self.selection_mode = selection_mode
        self.controls = AnnotateImageControlsAIO(
            controller=self.controller,
            refresh_layout_callback=self._create_layout,
            aio_id=aio_id
            )
        self.aio_id = self.controls.aio_id

        super().__init__(self.controls) # Equivalent to `html.Div([...])`
        self._define_callbacks()
    
    def _define_callbacks(self):
        """Define callbacks, called in constructor
        """        
        @callback(
            Output(self.ids.image(MATCH), 'children'),
            Output(self.ids.alert_label(MATCH), 'children'),
            Input(self.ids.dropdown(MATCH), 'value')
            )
        def change_label(dropdown_value):
            trigger_id = get_trigger_id()
            logger.debug(f"Trigger: '{trigger_id}'")

            is_initial = trigger_id == ""

            if is_initial:
                return self._create_image_layout(), self._create_existing_label_alert_layout()    
            
            elif trigger_id == self.ids.dropdown(MATCH)["subcomponent"]:
                # Dropdown was changed
                logger.debug(f"Dropdown changed: {dropdown_value}")
                if self.selection_mode == SelectionMode.SINGLE:
                    self.controller.store_label_single(dropdown_value[0])
                elif self.selection_mode == SelectionMode.MULTIPLE:
                    self.controller.store_label_multiple(dropdown_value)
                else:
                    raise NotImplementedError(f"Unknown selection mode: {self.selection_mode}")
                return no_update, no_update

            else:
                logger.debug(f"Unknown button pressed: {trigger_id}")
                return no_update, no_update
    
    def _create_layout(self):
        """Create layout for component
        """
        label = None
        if self.controller.curr is not None:
            if self.selection_mode == SelectionMode.SINGLE:
                label = self.controller.curr.label_single
            elif self.selection_mode == SelectionMode.MULTIPLE:
                label = self.controller.curr.label_multiple
            else:
                raise NotImplementedError(f"Unknown selection mode: {self.selection_mode}")
        
        dropdown = dcc.Dropdown(
            self.controller.labels, 
            value=label, 
            id=self.ids.dropdown(self.aio_id), 
            multi=self.selection_mode == SelectionMode.MULTIPLE
            )

        return dbc.Row([
            dbc.Col(id=self.ids.alert_label(self.aio_id), xs=12),
            dbc.Col([
                html.Div(id=self.ids.image(self.aio_id))
            ], md=6),
            dbc.Col([
                dropdown
            ], md=6)
        ])

    def _create_existing_label_alert_layout(self) -> Optional[dbc.Alert]:
        """Create layout for existing label
        """
        existing_label = None
        if self.controller.curr is not None:
            if self.selection_mode == SelectionMode.SINGLE:
                existing_label = self.controller.curr.label_single
            elif self.selection_mode == SelectionMode.MULTIPLE:
                existing_label = self.controller.curr.label_multiple
            else:
                raise NotImplementedError(f"Unknown selection mode: {self.selection_mode}")

        if existing_label is not None:
            if type(existing_label) == str and existing_label in self.controller.labels:
                return dbc.Alert(f"Existing annotation: {existing_label}", color="primary")
            elif type(existing_label) == list and all([l in self.controller.labels for l in existing_label]):
                return dbc.Alert(f"Existing annotation: {existing_label}", color="primary")
            else:
                return dbc.Alert(f"Existing unknown annotation: {existing_label}", color="danger")
        else:
            return None

    def _create_image_layout(self):
        """Create layout for the image
        """ 
        image = None
        if self.controller.curr is not None:
            image = self.controller.curr.image
        if image is None:
            return []
        fig = px.imshow(image)
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        return dcc.Graph(id="graph-styled-annotations", figure=fig)