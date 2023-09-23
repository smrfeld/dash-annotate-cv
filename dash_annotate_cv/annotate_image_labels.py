from dash_annotate_cv.annotate_image_labels_controller import ImageAnnotationController, ImageAnnotationOptions
from dash_annotate_cv.annotation_storage import AnnotationStorage, AnnotationWriter
from dash_annotate_cv.helpers import get_trigger_id
from dash_annotate_cv.image_source import ImageSource, ImageIterator, IndexAboveError, IndexBelowError
from dash_annotate_cv.label_source import LabelSource
from dash_annotate_cv.image_annotations import ImageAnnotations

from dash import Dash, Output, Input, State, html, dcc, callback, MATCH
import uuid
from typing import List, Optional, Dict
import plotly.express as px
import dash_bootstrap_components as dbc
from PIL import Image
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from enum import Enum
import datetime
import os


class AnnotateImageLabelsAIO(html.Div):
    """Annotation component for images
    """

    # A set of functions that create pattern-matching callbacks of the subcomponents
    class ids:
        buttons = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'buttons',
            'aio_id': aio_id
        }
        dropdown = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'dropdown',
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
        image = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'image',
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
        options: ImageAnnotationOptions = ImageAnnotationOptions()
        ):
        """Constructor

        Args:
            label_source (LabelSource): Source of labels
            image_source (ImageSource): Source of images
            annotation_storage (AnnotationStorage, optional): Where to store annotations. Defaults to AnnotationStorage().
            annotations_existing (Optional[ImageAnnotations], optional): Existing annotations to continue from, if any. Defaults to None.
            aio_id (Optional[str], optional): IDs for components. Defaults to None.
            options (Options, optional): Options. Defaults to Options().
        """
        self.controller = ImageAnnotationController(
            label_source=label_source,
            image_source=image_source,
            annotation_storage=annotation_storage,
            annotations_existing=annotations_existing,
            options=options
            )
        self._curr_image_layout, self._curr_button_layout, self._curr_alert_layout = None, None, None

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
    
    def _refresh_layout(self):
        # Update layout
        image = self.controller.curr.image if self.controller.curr is not None else None
        label = self.controller.curr.label_value if self.controller.curr is not None else None
        self._curr_image_layout = self._create_layout_for_image(image)                    
        self._curr_alert_layout = self._alert_for_existing_label(label)

    def _define_callbacks(self):
        """Define callbacks, called in constructor
        """        
        @callback(
            Output(self.ids.image(MATCH), 'children'),
            Output(self.ids.buttons(MATCH), 'children'),
            Input(self.ids.next_submit(MATCH), 'n_clicks'),
            Input(self.ids.next_skip(MATCH), 'n_clicks'),
            Input(self.ids.prev(MATCH), 'n_clicks'),
            Input(self.ids.next_missing_ann(MATCH), 'n_clicks'),
            Input(self.ids.dropdown(MATCH), 'value')
            )
        def submit_button(submit_n_clicks, skip_n_clicks, prev_n_clicks, next_missing_ann_n_clicks, dropdown_value):
            new_dropdown_value = dropdown_value
            trigger_id = get_trigger_id()
            print(f"Trigger: '{trigger_id}'")

            is_initial = trigger_id == "" and self.controller.curr is None

            try:
                if trigger_id == self.ids.next_submit(MATCH)["subcomponent"] or is_initial:
                    # Submit button was pressed
                    self.controller.store_label(dropdown_value)
                    self._refresh_layout()

                elif trigger_id == self.ids.next_skip(MATCH)["subcomponent"]:
                    # Skip button was pressed
                    self.controller.skip()
                    self._refresh_layout()

                elif trigger_id == self.ids.prev(MATCH)["subcomponent"]:
                    # Previous button was pressed
                    self.controller.previous()
                    self._refresh_layout()

                elif trigger_id == self.ids.next_missing_ann(MATCH)["subcomponent"]:
                    # Next missing annotation button was pressed
                    self.controller.skip_to_next_missing_ann()
                    self._refresh_layout()
                
                elif trigger_id == self.ids.dropdown(MATCH)["subcomponent"]:
                    # Dropdown was changed
                    pass

                else:
                    print(f"Unknown button pressed: {trigger_id}")

                if new_dropdown_value is not None and new_dropdown_value in self.controller.labels:
                    self._curr_button_layout = self._create_layout_buttons(
                        aio_id=self.aio_id, 
                        curr_selected_label=new_dropdown_value,
                        enable_dropdown=True,
                        enable_next_save=True, 
                        enable_prev=True, 
                        enable_skip=True, 
                        enable_skip_next_missing=True
                        )
                else:
                    self._curr_button_layout = self._create_layout_buttons(
                        aio_id=self.aio_id, 
                        curr_selected_label=new_dropdown_value,
                        enable_dropdown=True,
                        enable_next_save=False, 
                        enable_prev=True, 
                        enable_skip=True, 
                        enable_skip_next_missing=True
                        )

            except IndexAboveError:
                self._curr_image_layout = html.Div()
                self._curr_alert_layout = dbc.Alert("Finished all images",color="success")
                self._curr_button_layout = self._create_layout_buttons(
                    aio_id=self.aio_id, 
                    curr_selected_label=None,
                    enable_dropdown=False,
                    enable_next_save=False, 
                    enable_prev=True, 
                    enable_skip=False, 
                    enable_skip_next_missing=False
                    )

            except IndexBelowError:
                self._curr_image_layout = html.Div()
                self._curr_alert_layout = dbc.Alert("Start of images",color="danger")
                self._curr_button_layout = self._create_layout_buttons(
                    aio_id=self.aio_id, 
                    curr_selected_label=None,
                    enable_dropdown=False,
                    enable_next_save=True, 
                    enable_prev=False, 
                    enable_skip=True, 
                    enable_skip_next_missing=True
                    )

            print("Returning new dropdown value", new_dropdown_value)
            return self._curr_image_layout, self._curr_button_layout
    
    def _alert_for_existing_label(self, existing_label: Optional[str]) -> Optional[dbc.Alert]:
        """Create layout for existing label
        """
        if existing_label is not None and existing_label in self.controller.labels:
            return dbc.Alert(f"Existing annotation: {existing_label}", color="primary")
        else:
            return None

    def _create_layout(self, aio_id: str):
        """Create layout for component
        """        
        return dbc.Row([
            dbc.Col([
                html.Div(id=self.ids.image(aio_id))
            ], md=6),
            dbc.Col([
                self._create_layout_buttons(aio_id)
            ], md=6, id=self.ids.buttons(aio_id))
        ])

    def _create_layout_buttons(self, 
        aio_id: str, 
        curr_selected_label: Optional[str] = None, 
        enable_dropdown: bool = False, 
        enable_next_save: bool = False, 
        enable_prev: bool=False, 
        enable_skip: bool = False, 
        enable_skip_next_missing: bool = False
        ):
        """Create layout for buttons
        """        
        style_prev = {"width": "100%"} 
        style_next_save = {"width": "100%"} 
        style_skip = {"width": "100%"} 
        style_next_missing_annotation = {"width": "100%"} 
        style_dropdown = {}
        if not enable_prev:
            style_prev["display"] = "none"
        if not enable_next_save:
            style_next_save["display"] = "none"
        if not enable_skip:
            style_skip["display"] = "none"
        if not enable_skip_next_missing:
            style_next_missing_annotation["display"] = "none"
        if not enable_dropdown:
            style_dropdown["display"] = "none"

        if self.controller.curr is not None:
            no_images = self.controller.no_images
            title = f"Image {self.controller.curr.image_idx+1}/{no_images}"
        else:
            title = "Image"

        # Create components
        dropdown = dcc.Dropdown(
            self.controller.labels, 
            value=curr_selected_label, 
            id=self.ids.dropdown(aio_id), 
            style=style_dropdown,
            multi=self.controller.options.selection_mode == ImageAnnotationOptions.SelectionMode.MULTIPLE
            )
        prev_button = dbc.Button("Previous image", color="dark", id=self.ids.prev(aio_id), style=style_prev)
        next_button = dbc.Button("Next (save)", color="success", id=self.ids.next_submit(aio_id), style=style_next_save)
        skip_button = dbc.Button("Skip", color="dark", id=self.ids.next_skip(aio_id), style=style_skip)
        skip_to_next_button = dbc.Button("Skip to next missing annotation", color="warning", id=self.ids.next_missing_ann(aio_id), style=style_next_missing_annotation)

        return dbc.Col([
            html.H2(title),
            html.Div(self._curr_alert_layout),
            html.Hr(),
            dbc.Row(dropdown),
            html.Hr(style=style_dropdown),
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

    def _create_layout_for_image(self, image: Optional[Image.Image]):
        """Create layout for the image
        """        
        if image is None:
            return []
        fig = px.imshow(image)
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        return dcc.Graph(id="graph-styled-annotations", figure=fig)