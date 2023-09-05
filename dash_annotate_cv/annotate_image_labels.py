from dash_annotate_cv.annotation_storage import AnnotationStorage, AnnotationWriter
from dash_annotate_cv.helpers import get_trigger_id
from dash_annotate_cv.image_source import ImageSource, ImageIterator, IndexAboveError, IndexBelowError
from dash_annotate_cv.label_source import LabelSource

from dash import Dash, Output, Input, State, html, dcc, callback, MATCH
import uuid
from typing import List, Optional, Dict
import plotly.express as px
import dash_bootstrap_components as dbc
from PIL import Image
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig
from enum import Enum
import datetime
import os

@dataclass
class ImageAnnotations(DataClassDictMixin):

    @dataclass
    class Annotation(DataClassDictMixin):

        @dataclass
        class Label(DataClassDictMixin):
            single: Optional[str] = None
            multiple: Optional[List[str]] = None
            timestamp: Optional[float] = None
            author: Optional[str] = None

            class Config(BaseConfig):
                omit_none = True

        image_name: str
        label: Label
        history: Optional[List[Label]] = None
        
        class Config(BaseConfig):
            omit_none = True

    image_to_entry: Dict[str,Annotation]

class AnnotateImageLabelsAIO(html.Div):

    @dataclass
    class Options(DataClassDictMixin):

        class SelectionMode(Enum):
            SINGLE = "single"

        selection_mode: SelectionMode = SelectionMode.SINGLE
        store_timestamps: bool = True
        store_history: bool = True
        use_basename_for_image: bool = False
        author: Optional[str] = None

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

    # Make the ids class a public class
    ids = ids

    # Define the arguments of the All-in-One component
    def __init__(
        self,
        label_source: LabelSource,
        image_source: ImageSource,
        annotation_storage: AnnotationStorage = AnnotationStorage(),
        annotations_existing: Optional[ImageAnnotations] = None,
        markdown_props=None,
        dropdown_props=None,
        aio_id: Optional[str] = None,
        options: Options = Options()
        ):
        """MarkdownWithColorAIO is an All-in-One component that is composed
        of a parent `html.Div` with a `dcc.Dropdown` color picker ("`dropdown`") and a
        `dcc.Markdown` ("`markdown`") component as children.
        The markdown component's color is determined by the dropdown colorpicker.
        - `text` - The Markdown component's text (required)
        - `colors` - The colors displayed in the dropdown
        - `markdown_props` - A dictionary of properties passed into the dcc.Markdown component. See https://dash.plotly.com/dash-core-components/markdown for the full list.
        - `dropdown_props` - A dictionary of properties passed into the dcc.Dropdown component. See https://dash.plotly.com/dash-core-components/dropdown for the full list.
        - `aio_id` - The All-in-One component ID used to generate the markdown and dropdown components's dictionary IDs.

        The All-in-One component dictionary IDs are available as
        - MarkdownWithColorAIO.ids.dropdown(aio_id)
        - MarkdownWithColorAIO.ids.markdown(aio_id)
        """
        self.label_source = label_source
        self.labels = label_source.get_labels()
        self.image_source = image_source
        self.annotations = annotations_existing or ImageAnnotations(image_to_entry={})
        self.curr_image_name: Optional[str] = None
        self.options = options
        self.annotation_writer = AnnotationWriter(annotation_storage)
        self._curr_image_layout, self._curr_button_layout, self._curr_alert_layout, self.curr_image_idx = None, None, None, None

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

        # Merge user-supplied properties into default properties
        '''
        dropdown_props = dropdown_props.copy() if dropdown_props else {}
        if 'options' not in dropdown_props:
            dropdown_props['options'] = [{'label': i, 'value': i} for i in colors]
        dropdown_props['value'] = dropdown_props['options'][0]['value']

        # Merge user-supplied properties into default properties
        markdown_props = markdown_props.copy() if markdown_props else {} # copy the dict so as to not mutate the user's dict
        if 'style' not in markdown_props:
            markdown_props['style'] = {'color': dropdown_props['value']}
        if 'children' not in markdown_props:
            markdown_props['children'] = text
        
        # Define the component's layout
        super().__init__([  # Equivalent to `html.Div([...])`
            dcc.Dropdown(id=self.ids.dropdown(aio_id), **dropdown_props),
            dcc.Markdown(id=self.ids.markdown(aio_id), **markdown_props)
        ])
        '''

        super().__init__(self._create_layout(self.aio_id)) # Equivalent to `html.Div([...])`

        self._image_iterator = ImageIterator(self.image_source)
        self._define_callbacks()
    
    def _define_callbacks(self):
        
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

            is_initial = trigger_id == "" and self.curr_image_name is None

            try:
                if trigger_id == self.ids.next_submit(MATCH)["subcomponent"] or is_initial:
                    # Submit button was pressed

                    # Store the annotation
                    if self.curr_image_name is not None and dropdown_value is not None and dropdown_value in self.labels:

                        image_name = os.path.basename(self.curr_image_name) if self.options.use_basename_for_image else self.curr_image_name

                        # Label
                        label = ImageAnnotations.Annotation.Label(
                            single=dropdown_value,
                            timestamp=datetime.datetime.now().timestamp() if self.options.store_timestamps else None,
                            author=self.options.author
                            )

                        did_update = False
                        if image_name in self.annotations.image_to_entry:
                            ann = self.annotations.image_to_entry[image_name]
                            if ann.label != label:
                                ann.label = label
                                did_update = True
                        else:
                            ann = ImageAnnotations.Annotation(
                                image_name=self.curr_image_name,
                                label=label
                                )
                            self.annotations.image_to_entry[image_name] = ann
                            did_update = True

                        # Also add history
                        if did_update and self.options.store_history:
                            if ann.history is None:
                                ann.history = []
                            ann.history.append(label)

                    # Write
                    self.annotation_writer.write(self.annotations)

                    # Load the next image
                    self.curr_image_idx, self.curr_image_name, image = self._image_iterator.next()
                    self._curr_image_layout = self._create_layout_for_image(image)
                    
                    # Get annotation of new image
                    new_dropdown_value = self._get_existing_label_of_curr_image()
                    self._curr_alert_layout = self._alert_for_existing_dropdown(new_dropdown_value)

                elif trigger_id == self.ids.next_skip(MATCH)["subcomponent"]:
                    # Skip button was pressed
                    self.curr_image_idx, self.curr_image_name, image = self._image_iterator.next()
                    self._curr_image_layout = self._create_layout_for_image(image)
                    new_dropdown_value = self._get_existing_label_of_curr_image()
                    self._curr_alert_layout = self._alert_for_existing_dropdown(new_dropdown_value)

                elif trigger_id == self.ids.prev(MATCH)["subcomponent"]:
                    # Previous button was pressed
                    self.curr_image_idx, self.curr_image_name, image = self._image_iterator.prev()
                    self._curr_image_layout = self._create_layout_for_image(image)
                    new_dropdown_value = self._get_existing_label_of_curr_image()
                    self._curr_alert_layout = self._alert_for_existing_dropdown(new_dropdown_value)

                elif trigger_id == self.ids.next_missing_ann(MATCH)["subcomponent"]:
                    # Next missing annotation button was pressed
                    image = None
                    while self.curr_image_name in self.annotations.image_to_entry:
                        self.curr_image_idx, self.curr_image_name, image = self._image_iterator.next()
                    if image is not None:
                        # Changed image
                        self._curr_image_layout = self._create_layout_for_image(image)
                        new_dropdown_value = self._get_existing_label_of_curr_image()
                        self._curr_alert_layout = self._alert_for_existing_dropdown(new_dropdown_value)

                elif trigger_id == self.ids.dropdown(MATCH)["subcomponent"]:
                    # Dropdown was changed
                    pass

                else:
                    print(f"Unknown button pressed: {trigger_id}")

                if new_dropdown_value is not None and new_dropdown_value in self.labels:
                    self._curr_button_layout = self._create_layout_buttons(
                        aio_id=self.aio_id, 
                        curr_dropdown=new_dropdown_value,
                        enable_dropdown=True,
                        enable_next_save=True, 
                        enable_prev=True, 
                        enable_skip=True, 
                        enable_skip_next_missing=True
                        )
                else:
                    self._curr_button_layout = self._create_layout_buttons(
                        aio_id=self.aio_id, 
                        curr_dropdown=new_dropdown_value,
                        enable_dropdown=True,
                        enable_next_save=False, 
                        enable_prev=True, 
                        enable_skip=True, 
                        enable_skip_next_missing=True
                        )

            except IndexAboveError:
                self._curr_image_layout = html.Div()
                self._curr_button_layout = self._create_layout_buttons(
                    aio_id=self.aio_id, 
                    curr_dropdown=None,
                    enable_dropdown=False,
                    enable_next_save=False, 
                    enable_prev=True, 
                    enable_skip=False, 
                    enable_skip_next_missing=False
                    )
                self._curr_alert_layout = dbc.Alert("Finished all images",color="success")

            except IndexBelowError:
                self._curr_image_layout = html.Div()
                self._curr_button_layout = self._create_layout_buttons(
                    aio_id=self.aio_id, 
                    curr_dropdown=None,
                    enable_dropdown=False,
                    enable_next_save=True, 
                    enable_prev=False, 
                    enable_skip=True, 
                    enable_skip_next_missing=True
                    )
                self._curr_alert_layout = dbc.Alert("Start of images",color="danger")

            print("Returning new dropdown value", new_dropdown_value)
            return self._curr_image_layout, self._curr_button_layout
    
    def _alert_for_existing_dropdown(self, new_dropdown_value: Optional[str]):
        if new_dropdown_value is not None and new_dropdown_value in self.labels:
            return dbc.Alert(f"Existing annotation: {new_dropdown_value}", color="primary")
        else:
            return None

    def _get_existing_label_of_curr_image(self) -> Optional[str]:
        if self.curr_image_name in self.annotations.image_to_entry:
            entry = self.annotations.image_to_entry[self.curr_image_name]
            if entry.label.single is not None and entry.label.single in self.labels:
                return entry.label.single
        return None

    def _create_layout(self, aio_id: str):
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
        curr_dropdown: Optional[str] = None, 
        enable_dropdown: bool = False, 
        enable_next_save: bool = False, 
        enable_prev: bool=False, 
        enable_skip: bool = False, 
        enable_skip_next_missing: bool = False
        ):
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

        if hasattr(self,"_image_iterator") and self._image_iterator is not None and self.curr_image_idx is not None:
            no_images = self._image_iterator.no_images
            title = f"Image {self.curr_image_idx+1}/{no_images}"
        else:
            title = "Image"

        return dbc.Col([
            html.H2(title),
            html.Div(self._curr_alert_layout),
            html.Hr(),
            dbc.Row(dcc.Dropdown(self.labels, value=curr_dropdown, id=self.ids.dropdown(aio_id), style=style_dropdown)),
            html.Hr(style=style_dropdown),
            dbc.Row([
                dbc.Col(dbc.Button("Previous image", color="dark", id=self.ids.prev(aio_id), style=style_prev), md=6),
                dbc.Col(dbc.Button("Next (save)", color="success", id=self.ids.next_submit(aio_id), style=style_next_save), md=6)
                ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([],md=6),
                dbc.Col(dbc.Button("Skip", color="dark", id=self.ids.next_skip(aio_id), style=style_skip), md=6),
                ]),
            dbc.Row([
                dbc.Col([],md=6),
                dbc.Col(dbc.Button("Skip to next missing annotation", color="warning", id=self.ids.next_missing_ann(aio_id), style=style_next_missing_annotation), md=6),
            ])
        ])

    def _create_layout_for_image(self, image: Image.Image):
        fig = px.imshow(image)
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        return dcc.Graph(id="graph-styled-annotations", figure=fig)