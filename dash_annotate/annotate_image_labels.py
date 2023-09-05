from dash_annotate.annotation_storage import AnnotationStorage, AnnotationWriter
from dash_annotate.image_source import ImageSource, ImageIterator
from dash_annotate.label_source import LabelSource

from dash import Dash, Output, Input, State, html, dcc, callback, MATCH
import uuid
from typing import List, Optional, Dict
import plotly.express as px
import dash_bootstrap_components as dbc
from PIL import Image
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from enum import Enum
import dash
import json
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

        image_name: str
        label: Label
        history: Optional[List[Label]] = None
    
    image_to_entry: Dict[str,Annotation]

class AnnotateImageLabelsAIO(html.Div):

    @dataclass
    class Options(DataClassDictMixin):

        class SelectionMode(Enum):
            SINGLE = "single"
            MULTIPLE = "multiple"

        selection_mode: SelectionMode = SelectionMode.SINGLE
        store_timestamps: bool = True
        store_history: bool = True
        use_basename_for_image: bool = False
        author: Optional[str] = None

    # A set of functions that create pattern-matching callbacks of the subcomponents
    class ids:
        dropdown = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'dropdown',
            'aio_id': aio_id
        }
        markdown = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'markdown',
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
        annotation_storage: AnnotationStorage,
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

        # Allow developers to pass in their own `aio_id` if they're
        # binding their own callback to a particular component.
        if aio_id is None:
            # Otherwise use a uuid that has virtually no chance of collision.
            # Uuids are safe in dash deployments with processes
            # because this component's callbacks
            # use a stateless pattern-matching callback:
            # The actual ID does not matter as long as its unique and matches
            # the PMC `MATCH` pattern..
            aio_id = str(uuid.uuid4())

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

        super().__init__(self._create_layout(aio_id)) # Equivalent to `html.Div([...])`

        self._image_iterator = ImageIterator(self.image_source)
        self._define_callbacks()
    
    def _define_callbacks(self):
        
        @callback(
            Output(self.ids.image(MATCH), 'children'),
            Input(self.ids.next_submit(MATCH), 'n_clicks'),
            Input(self.ids.next_skip(MATCH), 'n_clicks'),
            Input(self.ids.prev(MATCH), 'n_clicks'),
            Input(self.ids.next_missing_ann(MATCH), 'n_clicks'),
            )
        def submit_button(submit_n_clicks, skip_n_clicks, prev_n_clicks, next_missing_ann_n_clicks):
            # Figure out which button was pressed
            ctx = dash.callback_context
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if button_id != "":
                button_id = json.loads(button_id)["subcomponent"]
            print(f"Clicked button: '{button_id}'")

            try:
                if button_id == self.ids.next_submit(MATCH)["subcomponent"] or button_id == "":
                    # Submit button was pressed

                    # Store the annotation
                    if self.curr_image_name is not None:
                        ann = ImageAnnotations.Annotation(
                            image_name=self.curr_image_name,
                            label=ImageAnnotations.Annotation.Label(
                                single=self.labels[self.ids.dropdown(MATCH)["value"]],
                                timestamp=datetime.datetime.now().timestamp() if self.options.store_timestamps else None,
                                author=self.options.author
                                )
                            )
                        image_name = os.path.basename(self.curr_image_name) if self.options.use_basename_for_image else self.curr_image_name
                        self.annotations.image_to_entry[image_name] = ann

                    # Write
                    self.annotation_writer.write(self.annotations)

                    # Load the next image
                    self.curr_image_name, image = self._image_iterator.next()
                
                elif button_id == self.ids.next_skip(MATCH)["subcomponent"]:
                    # Skip button was pressed
                    self.curr_image_name, image = self._image_iterator.next()
                
                elif button_id == self.ids.prev(MATCH)["subcomponent"]:
                    # Previous button was pressed
                    self.curr_image_name, image = self._image_iterator.prev()
                
                elif button_id == self.ids.next_missing_ann(MATCH)["subcomponent"]:
                    # Next missing annotation button was pressed
                    self.curr_image_name, image = self._image_iterator.next()
                    while self.curr_image_name in self.annotations.image_to_entry:
                        self.curr_image_name, image = self._image_iterator.next()

                else:
                    raise NotImplementedError(f"Unknown button pressed: {button_id}")

                return self._create_layout_for_image(image)
            except StopIteration:
                return html.Div("No more images")

    def _create_layout(self, aio_id: str):
        return dbc.Row([
            dbc.Col([
                html.Div(id=self.ids.image(aio_id))
            ], md=6),
            dbc.Col([
                dbc.Row(dcc.Dropdown(self.labels, id=self.ids.dropdown(MATCH)['subcomponent'])),
                self._create_next_prev_row(aio_id),
                self._create_next_alt_row(aio_id)
            ], md=6)
        ])

    def _create_next_prev_row(self, aio_id: str):
        return dbc.Row([
            dbc.Col(dbc.Button("Previous image", color="secondary", id=self.ids.prev(aio_id), style={"width": "100%"}), md=6),
            dbc.Col(dbc.Button("Next (save)", color="success", id=self.ids.next_submit(aio_id), style={"width": "100%"}), md=6)
        ])

    def _create_next_alt_row(self, aio_id: str):
        return dbc.Row([
            dbc.Col(dbc.Button("Skip", color="secondary", id=self.ids.next_skip(aio_id), style={"width": "100%"}), md=6),
            dbc.Col(dbc.Button("Skip to missing annotation", color="warning", id=self.ids.next_missing_ann(aio_id), style={"width": "100%"}), md=6),
        ])

    def _create_layout_for_image(self, image: Image.Image):
        fig = px.imshow(image)
        return dcc.Graph(id="graph-styled-annotations", figure=fig)