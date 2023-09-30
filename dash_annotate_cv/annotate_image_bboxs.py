from dash_annotate_cv.annotate_image_controller import AnnotateImageController, AnnotateImageOptions, ImageAnn, NoCurrLabelError, InvalidLabelError, load_image_anns_if_exist, Bbox, BboxUpdate
from dash_annotate_cv.helpers import get_trigger_id
from dash_annotate_cv.image_source import ImageSource, IndexAboveError, IndexBelowError
from dash_annotate_cv.label_source import LabelSource
from dash_annotate_cv.image_annotations import ImageAnnotations
from dash_annotate_cv.annotation_storage import AnnotationStorage

from typing import Optional
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, no_update, callback, State
from skimage import data
import json
from dash import Output, Input, html, dcc, callback, MATCH, ALL
import uuid
from typing import Optional, Union, List, Dict
import plotly.express as px
import dash_bootstrap_components as dbc
from PIL import Image
from dataclasses import dataclass
import logging
import plotly.graph_objects as go
import dash 


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
        highlight_bbox = lambda aio_id, idx: {
            'component': 'AnnotateImageBboxsAIO',
            'subcomponent': 'highlight_bbox',
            'aio_id': aio_id,
            'idx': idx
        }
        delete_button = lambda aio_id, idx: {
            'component': 'AnnotateImageBboxsAIO',
            'subcomponent': 'delete_button',
            'aio_id': aio_id,
            'idx': idx
        }
        dropdown = lambda aio_id, idx: {
            'component': 'AnnotateImageBboxsAIO',
            'subcomponent': 'dropdown',
            'aio_id': aio_id,
            'idx': idx
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

        self.options = options
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
            dbc.Col(html.Div("No bboxs", id=self.ids.description(aio_id)), md=6)
        ])
    
    def _create_layout_for_curr_image(self):
        """Create layout for the image
        """        
        image = self.controller.curr.image if self.controller.curr is not None else None
        if image is None:
            return []
        fig = px.imshow(image)
        fig.update_layout(
            dragmode="drawrect",
            clickmode='event+select'
            )
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        return dcc.Graph(id=self.ids.graph_picture(self.aio_id), figure=fig)
    
    def _create_bbox_layout(self):
        if self.controller.curr is None:
            logger.debug("Creating bbox layout - no curr image")
            return no_update
        
        if self.controller.curr.bboxs is None:
            logger.debug("Creating bbox layout - no bboxs")
            bbox_list_group = []
        else:
            logger.debug(f"Creating bbox layout - num bboxs: {len(self.controller.curr.bboxs)}")
            bbox_list_group = [
                self._create_list_group_for_bbox_layout(bbox,idx)
                for idx,bbox in enumerate(self.controller.curr.bboxs)
                ]
        return dbc.ListGroup(bbox_list_group)

    def _create_list_group_for_bbox_layout(self, bbox: Bbox, bbox_idx: int):
        xyxy_label = "(%s)" % ",".join([str(int(x)) for x in bbox.xyxy])
        dropdown = dcc.Dropdown(
            self.controller.labels, 
            value=bbox.class_name, 
            id=self.ids.dropdown(self.aio_id, bbox_idx), 
            )

        button_delete = dbc.Button(
            "Delete", 
            color="danger", 
            size="sm", 
            className="mr-1",
            id=self.ids.delete_button(self.aio_id, bbox_idx)
            )

        button_highlight = dbc.Button(
            "Highlight", 
            color="primary", 
            size="sm", 
            className="mr-1",
            id=self.ids.highlight_bbox(self.aio_id, bbox_idx)
            )

        return dbc.ListGroupItem([
            dbc.Row([
                dbc.Col(dropdown, lg=3, md=6),
                dbc.Col(xyxy_label, lg=3, md=6),
                dbc.Col(button_highlight, lg=3, md=6),
                dbc.Col(button_delete, lg=3, md=6)
                ])
            ])

    def _define_callbacks(self):
        """Define callbacks
        """        
        logger.debug("Defining callbacks")
        @callback(
            Output(self.ids.description(MATCH), 'children'),
            Output(self.ids.graph_picture(MATCH), "figure"),
            Input(self.ids.graph_picture(MATCH), "relayoutData"),
            Input(self.ids.graph_picture(MATCH), "selectedData"),
            Input(self.ids.delete_button(MATCH, ALL), "n_clicks"),
            Input(self.ids.highlight_bbox(MATCH, ALL), "n_clicks"),
            Input(self.ids.dropdown(MATCH, ALL), "value"),
            State(self.ids.graph_picture(MATCH), "figure")
            )
        def update(relayout_data, click_data, n_clicks_delete, n_clicks_select, dropdown_value, figure):

            trigger_id, idx = get_trigger_id()
            logger.debug(f"Update: trigger ID: {trigger_id} idx: {idx}")

            if trigger_id == "delete_button":
                logger.debug("Pressed delete_button")
                assert idx is not None, "idx should not be None"
                self._handle_delete_button_pressed(idx)
                figure['layout']['shapes'] = self._create_curr_figure_shapes()
                return self._create_bbox_layout(), figure

            elif trigger_id == "highlight_bbox":
                logger.debug("Pressed highlight_bbox")
                assert idx is not None, "idx should not be None"
                shape = figure['layout']['shapes'][idx]
                logger.debug(shape)
                if shape['fillcolor'] in ['rgba(0,0,0,0)','rgba(0, 0, 0, 0)']:
                    shape['fillcolor'] = 'rgba(255,0,0,0.3)'
                    shape['line']['color'] = 'rgba(255,0,0,1)'
                else:
                    shape['fillcolor'] = 'rgba(0,0,0,0)'
                    shape['line']['color'] = '#444'
                return no_update, figure

            elif trigger_id == "dropdown":
                logger.debug("Changed dropdown")
                assert idx is not None, "idx should not be None"

                # Change the value
                self.controller.update_bbox(BboxUpdate(idx, None, dropdown_value[0]))
                figure['layout']['shapes'][idx] = self._bbox_to_shape(self._curr_bboxs[idx])
                return no_update, figure

            elif trigger_id == "graph_picture":
                logger.debug(f"click_data: {click_data}")

                if relayout_data is not None and "shapes" in relayout_data:
                    # A new box was drawn
                    # We receive all boxes from the data
                    self._handle_relayout_new_box_drawn(relayout_data)
                    return self._create_bbox_layout(), no_update
                elif relayout_data is not None and "shapes" in " ".join(list(relayout_data.keys())):
                    # A box was updated
                    self._handle_relaxout_box_updated(relayout_data)
                    return self._create_bbox_layout(), no_update
                else:
                    return no_update, no_update
            else:
                logger.warning(f"Unrecognized trigger ID: {trigger_id}")
                return no_update, no_update
                
        logger.debug("Defined callbacks")

    def _create_curr_figure_shapes(self) -> List:
        return self._bboxs_to_shapes(self._curr_bboxs)

    def _handle_delete_button_pressed(self, idx: int):
        logger.debug(f"Deleting bbox idx: {idx}")
        self.controller.delete_bbox(idx)

    def _handle_relayout_new_box_drawn(self, relayout_data: Dict):
        bboxs_new = self._relayout_data_to_bboxs(relayout_data)
        self.controller.set_bboxs(bboxs_new)

    def _handle_relaxout_box_updated(self, relayout_data: Dict):
        update = self._relayout_data_to_bbox_update(relayout_data)
        self.controller.update_bbox(update)

    @property
    def _curr_bboxs(self) -> List[Bbox]:
        if self.controller.curr is None:
            return []
        return self.controller.curr.bboxs or []

    def _shape_to_bbox(self, shape: Dict) -> Bbox:
        xyxy: List[float] = [ shape[c] for c in ["x0","y0","x1","y1"] ]
        return Bbox(xyxy, None)

    def _relayout_data_to_bboxs(self, relayout_data: Dict) -> List[Bbox]:
        return [ self._shape_to_bbox(bbox) for bbox in relayout_data["shapes"] ]

    def _relayout_data_to_bbox_update(self, relayout_data: Dict) -> BboxUpdate:
        # Parse shapes[0].x1 -> 0 from the brackets
        label = list(relayout_data.keys())[0]
        box_idx = int(label.split(".")[0].replace("shapes[","").replace("]",""))
        shapes_label = "shapes[%d]" % box_idx
        xyxy = [ relayout_data["%s.%s" % (shapes_label,label)] for label in ["x0","y0","x1","y1"] ]
        return BboxUpdate(box_idx, xyxy, None)

    def _bbox_to_shape(self, bbox: Bbox) -> Dict:
        if bbox.class_name is None:
            line_color = '#444'
        else:
            rgb = self.options.get_assign_color_for_class(bbox.class_name)
            line_color = 'rgba(%d,%d,%d,1)' % rgb

        return {
            'editable': True, 
            'visible': True, 
            'showlegend': False, 
            'legend': 'legend', 
            'legendgroup': '', 
            'legendgrouptitle': {'text': ''}, 
            'legendrank': 1000, 
            'label': {'text': '', 'texttemplate': ''}, 
            'xref': 'x', 
            'yref': 'y', 
            'layer': 'above', 
            'opacity': 1, 
            'line': {'color': line_color, 'width': 4, 'dash': 'solid'}, 
            'fillcolor': 'rgba(0,0,0,0)', 
            'fillrule': 'evenodd', 
            'type': 
            'rect', 
            'x0': bbox.xyxy[0], 
            'y0': bbox.xyxy[1], 
            'x1': bbox.xyxy[2], 
            'y1': bbox.xyxy[3]
            }

    def _bboxs_to_shapes(self, bboxs: List[Bbox]) -> List[Dict]:
        return [ self._bbox_to_shape(bbox) for bbox in bboxs ]
        
