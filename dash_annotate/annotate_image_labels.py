from dash_annotate.image_source import ImageSource
from dash_annotate.label_source import LabelSource

from dash import Dash, Output, Input, State, html, dcc, callback, MATCH
import uuid
from typing import List
import plotly.express as px
import dash_bootstrap_components as dbc
from PIL import Image

class AnnotateImageLabelsAIO(html.Div):

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
        submit = lambda aio_id: {
            'component': 'AnnotateImageLabelsAIO',
            'subcomponent': 'submit',
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
        markdown_props=None,
        dropdown_props=None,
        aio_id=None
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
        self.image_source = image_source

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

        self._image_iterator = self.image_source.iterate_over_images()
        self._define_callbacks()
    
    def _define_callbacks(self):
        
        @callback(
            Output(self.ids.image(MATCH), 'children'),
            Input(self.ids.submit(MATCH), 'n_clicks')
        )
        def submit_button(submit_n_clicks):
            try:
                image = next(self._image_iterator)
                return self._create_layout_for_image(image)
            except StopIteration:
                return html.Div("No more images")

    def _create_layout(self, aio_id: str):
        return [
            html.H3("Drag and draw annotations"),
            dbc.Row([
                dbc.Col([
                    html.Div(id=self.ids.image(aio_id))
                ], md=6),
                dbc.Col([
                    dbc.Button("Submit", id=self.ids.submit(aio_id), className="mr-2")
                ], md=6)
            ])
            ]

    def _create_layout_for_image(self, image: Image.Image):
        fig = px.imshow(image)
        return dcc.Graph(id="graph-styled-annotations", figure=fig)
    
    # Define this component's stateless pattern-matching callback
    # that will apply to every instance of this component.
    @callback(
        Output(ids.markdown(MATCH), 'style'),
        Input(ids.dropdown(MATCH), 'value'),
        State(ids.markdown(MATCH), 'style'),
    )
    def update_markdown_style(color, existing_style):
        existing_style['color'] = color
        return existing_style