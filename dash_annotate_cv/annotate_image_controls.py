from dash_annotate_cv.annotate_image_controller import AnnotateImageController
from dash_annotate_cv.helpers import get_trigger_id
from dash_annotate_cv.image_source import IndexAboveError, IndexBelowError

from dash import Output, Input, html, callback, MATCH
import uuid
from typing import Optional, Union, List, Callable
import dash_bootstrap_components as dbc
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


class AnnotateImageControlsAIO(html.Div):
    """Annotation component for images
    """

    # A set of functions that create pattern-matching callbacks of the subcomponents
    class ids:
        title = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'title',
            'aio_id': aio_id
        }
        alert = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'alert',
            'aio_id': aio_id
        }
        next_submit = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'next_submit',
            'aio_id': aio_id
        }
        next_skip = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'next_skip',
            'aio_id': aio_id
        }
        prev = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'prev',
            'aio_id': aio_id
        }
        next_missing_ann = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'next_missing_ann',
            'aio_id': aio_id
        }
        content = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'content',
            'aio_id': aio_id
        }

    ids = ids

    def __init__(
        self,
        controller: AnnotateImageController,
        refresh_layout_callback: Callable[[], dbc.Row],
        aio_id: Optional[str] = None
        ):
        self.controller = controller
        self._refresh_layout_callback = refresh_layout_callback
        
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

        super().__init__(self._create_layout()) # Equivalent to `html.Div([...])`
        self._define_callbacks()
    
    def _define_callbacks(self):
        """Define callbacks, called in constructor
        """        
        @callback(
            Output(self.ids.title(MATCH), 'children'),
            Output(self.ids.content(MATCH), 'children'),
            Output(self.ids.alert(MATCH), 'children'),
            Input(self.ids.next_submit(MATCH), 'n_clicks'),
            Input(self.ids.next_skip(MATCH), 'n_clicks'),
            Input(self.ids.prev(MATCH), 'n_clicks'),
            Input(self.ids.next_missing_ann(MATCH), 'n_clicks')
            )
        def button_press(submit_n_clicks, skip_n_clicks, prev_n_clicks, next_missing_ann_n_clicks):
            trigger_id, _ = get_trigger_id()
            logger.debug(f"Trigger: '{trigger_id}'")

            is_initial = trigger_id == ""
            content_layout, alert_layout = None, None

            try:
                if is_initial:
                    # Initial state
                    content_layout = self._refresh_layout_callback()
                
                elif trigger_id == self.ids.next_submit(MATCH)["subcomponent"]:
                    # Submit button was pressed
                    self.controller.next_image()
                    content_layout = self._refresh_layout_callback()

                elif trigger_id == self.ids.next_skip(MATCH)["subcomponent"]:
                    # Skip button was pressed
                    self.controller.next_image()
                    content_layout = self._refresh_layout_callback()

                elif trigger_id == self.ids.prev(MATCH)["subcomponent"]:
                    # Previous button was pressed
                    self.controller.previous_image()
                    content_layout = self._refresh_layout_callback()

                elif trigger_id == self.ids.next_missing_ann(MATCH)["subcomponent"]:
                    # Next missing annotation button was pressed
                    self.controller.skip_to_next_missing_ann()
                    content_layout = self._refresh_layout_callback()
                
                else:
                    logger.debug(f"Unknown button pressed: {trigger_id}")

            except IndexAboveError:
                alert_layout = dbc.Alert("Finished all images",color="success")

            except IndexBelowError:
                alert_layout = dbc.Alert("Start of images",color="danger")

            title_layout = self._create_title_layout()

            return title_layout, content_layout, alert_layout
    
    def _create_layout(self):
        """Create layout for component
        """        
        return dbc.Row([
            dbc.Row([
                dbc.Col(
                    html.Div(id=self.ids.title(self.aio_id)),
                    md=6),
                dbc.Col(
                    self._create_layout_buttons(self.aio_id),
                    md=6),
            ]),
            dbc.Col(html.Hr(), xs=12),
            dbc.Col(id=self.ids.alert(self.aio_id), xs=12),
            dbc.Col(id=self.ids.content(self.aio_id), xs=12)
        ])

    @dataclass
    class EnableButtons:
        """Layout for buttons
        """ 
        prev_btn: bool = True
        next_btn: bool = True
        skip_btn: bool = True
        skip_to_next_btn: bool = True

    def _create_layout_buttons(self, 
        aio_id: str, 
        enable: EnableButtons = EnableButtons()
        ):
        """Create layout for buttons
        """ 
        style_prev = {"width": "100%"} 
        style_next_save = {"width": "100%"} 
        style_skip = {"width": "100%"} 
        style_next_missing_annotation = {"width": "100%"} 
        if not enable.prev_btn:
            style_prev["display"] = "none"
        if not enable.next_btn:
            style_next_save["display"] = "none"
        if not enable.skip_btn:
            style_skip["display"] = "none"
        if not enable.skip_to_next_btn:
            style_next_missing_annotation["display"] = "none"

        # Create components
        prev_button = dbc.Button("Previous image", color="dark", id=self.ids.prev(aio_id), style=style_prev)
        next_button = dbc.Button("Next (save)", color="success", id=self.ids.next_submit(aio_id), style=style_next_save)
        skip_button = dbc.Button("Skip", color="dark", id=self.ids.next_skip(aio_id), style=style_skip)
        skip_to_next_button = dbc.Button("Skip to next missing annotation", color="warning", id=self.ids.next_missing_ann(aio_id), style=style_next_missing_annotation)

        return dbc.Col([
            dbc.Row([
                dbc.Col(prev_button, md=6),
                dbc.Col(next_button, md=6)
                ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([],md=6),
                dbc.Col(skip_button, md=6),
                ]),
            dbc.Row([
                dbc.Col([],md=6),
                dbc.Col(skip_to_next_button, md=6),
            ])
        ])

    def _create_title_layout(self):
        if self.controller.curr is not None:
            no_images = self.controller.no_images
            title = f"Image {self.controller.curr.image_idx+1}/{no_images}"
        else:
            title = "Image"
        return html.H2(title)