from dash_annotate_cv.annotate_image_controller import AnnotateImageController, AnnotateImageOptions, Bbox, BboxUpdate, NoUpdate
from dash_annotate_cv.annotate_image_controls import AnnotateImageControlsAIO
from dash_annotate_cv.helpers import get_trigger_id, Xyxy
from dash_annotate_cv.image_source import ImageSource
from dash_annotate_cv.label_source import LabelSource
from dash_annotate_cv.image_annotations import ImageAnnotations
from dash_annotate_cv.annotation_storage import AnnotationStorage

from typing import Optional
import plotly.express as px
from dash import dcc, html, Input, Output, no_update, callback, State
from dash import Output, Input, html, dcc, callback, MATCH, ALL
from typing import Optional, List, Dict, Any
import plotly.express as px
import dash_bootstrap_components as dbc
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
        alert = lambda aio_id: {
            'component': 'AnnotateImageBboxsAIO',
            'subcomponent': 'alert',
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
        """Constructor

        Args:
            label_source (LabelSource): Label source
            image_source (ImageSource): Image source
            annotation_storage (AnnotationStorage, optional): Storage. Defaults to AnnotationStorage().
            annotations_existing (Optional[ImageAnnotations], optional): Existing annotations. Defaults to None.
            aio_id (Optional[str], optional): AIO Id to use for components. Defaults to None.
            options (AnnotateImageOptions, optional): Options. Defaults to AnnotateImageOptions().
        """        
        options.check_valid()

        self.controller = AnnotateImageController(
            label_source=label_source,
            image_source=image_source,
            annotation_storage=annotation_storage,
            annotations_existing=annotations_existing,
            options=options
            )
        self._curr_image_layout = None
        self.converter = BboxToShapeConverter(options=options)
        self.controls = AnnotateImageControlsAIO(
            controller=self.controller,
            refresh_layout_callback=self._create_layout,
            aio_id=aio_id
            )
        self.aio_id = self.controls.aio_id

        super().__init__(self.controls) # Equivalent to `html.Div([...])`
        self._define_callbacks()

    def _create_layout(self):
        """Create layout for component
        """
        logger.debug("Creating layout for component")

        self._curr_image_layout = self._create_layout_for_curr_image()  

        return dbc.Row([
            dbc.Col([
                html.Div(self._curr_image_layout, id=self.ids.image(self.aio_id))
            ], md=6),
            dbc.Col([
                html.Div(id=self.ids.alert(self.aio_id)),
                html.Div(id=self.ids.description(self.aio_id))
                ], md=6)
        ])

    def _create_layout_for_curr_image(self):
        """Create layout for the image
        """        
        image = self.controller.curr.image if self.controller.curr is not None else None
        if image is None:
            return []
        fig = px.imshow(image)
        rgb = self.controller.options.default_bbox_color
        line_color = 'rgba(%d,%d,%d,1)' % rgb
        fig.update_layout(
            dragmode="drawrect",
            newshape=dict(line_color=line_color)
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
                dbc.Col(dropdown, lg=4, md=6),
                dbc.Col(xyxy_label, lg=4, md=6),
                dbc.Col(button_highlight, lg=2, md=6),
                dbc.Col(button_delete, lg=2, md=6)
                ])
            ])

    def _create_alert_layout(self):
        alerts = []
        
        # No bboxs
        if len(self.controller.curr_bboxs) == 0:
            alerts.append(dbc.Alert("Start by drawing a bounding box", color="primary"))
        
        # Bboxs without labels
        for bbox in self.controller.curr_bboxs:
            if bbox.class_name is None:
                alerts.append(dbc.Alert("All bounding boxes must have labels", color="warning"))
                break

        return alerts

    def _define_callbacks(self):
        """Define callbacks
        """        
        logger.debug("Defining callbacks")
        @callback(
            Output(self.ids.description(MATCH), 'children'),
            Output(self.ids.graph_picture(MATCH), "figure"),
            Output(self.ids.alert(MATCH), "children"),
            Input(self.ids.graph_picture(MATCH), "relayoutData"),
            Input(self.ids.delete_button(MATCH, ALL), "n_clicks"),
            Input(self.ids.highlight_bbox(MATCH, ALL), "n_clicks"),
            Input(self.ids.dropdown(MATCH, ALL), "value"),
            State(self.ids.graph_picture(MATCH), "figure")
            )
        def update(relayout_data, n_clicks_delete, n_clicks_select, dropdown_value, figure):

            trigger_id, idx = get_trigger_id()
            logger.debug(f"Update: trigger ID: {trigger_id} idx: {idx}")

            if trigger_id == "delete_button":
                logger.debug("Pressed delete_button")
                assert idx is not None, "idx should not be None"
                update = self._handle_delete_button_pressed(idx, figure)

            elif trigger_id == "highlight_bbox":
                logger.debug("Pressed highlight_bbox")
                assert idx is not None, "idx should not be None"
                update = self._handle_highlight_button_pressed(idx, figure)

            elif trigger_id == "dropdown":
                logger.debug(f"Changed dropdown to {dropdown_value}")
                assert idx is not None, "idx should not be None"
                update = self._handle_dropdown_changed(idx, dropdown_value[idx], figure)

            elif trigger_id == "graph_picture":

                if relayout_data is not None and "shapes" in relayout_data:
                    # A new box was drawn
                    # We receive all boxes from the data
                    update = self._handle_new_box_drawn(relayout_data)
                elif relayout_data is not None and "shapes" in " ".join(list(relayout_data.keys())):
                    # A box was updated
                    update = self._handle_box_updated(relayout_data)
                else:
                    logger.warning(f"Unrecognized trigger for {trigger_id}")
                    # Just draw latest
                    self.converter.refresh_figure_shapes(figure, self.controller.curr_bboxs)
                    update = AnnotateImageBboxsAIO.Update(self._create_bbox_layout(), figure, self._create_alert_layout())
            else:
                logger.warning(f"Unrecognized trigger ID: {trigger_id}")
                # Just draw latest
                self.converter.refresh_figure_shapes(figure, self.controller.curr_bboxs)
                update = AnnotateImageBboxsAIO.Update(self._create_bbox_layout(), figure, self._create_alert_layout())
            
            return update.bbox_layout, update.figure, update.alert

        logger.debug("Defined callbacks")

    @dataclass
    class Update:
        bbox_layout: Any
        figure: Any
        alert: Any

    def _handle_delete_button_pressed(self, idx: int, figure: Dict) -> Update:
        logger.debug(f"Deleting bbox idx: {idx}")
        self.controller.delete_bbox(idx)
        self.converter.refresh_figure_shapes(figure, self.controller.curr_bboxs)
        return AnnotateImageBboxsAIO.Update(self._create_bbox_layout(), figure, self._create_alert_layout())

    def _handle_highlight_button_pressed(self, idx: int, figure: Dict) -> Update:
        self.controller.curr_bboxs[idx].is_highlighted = not self.controller.curr_bboxs[idx].is_highlighted
        self.converter.refresh_figure_shapes(figure, self.controller.curr_bboxs)
        return AnnotateImageBboxsAIO.Update(no_update, figure, self._create_alert_layout())

    def _handle_dropdown_changed(self, idx: int, dropdown_value_new: str, figure: Dict) -> Update:
        if type(dropdown_value_new) == list:
            logger.warning("Dropdown value is list, expected string")
            return AnnotateImageBboxsAIO.Update(no_update, no_update, self._create_alert_layout())
        assert idx is not None, "idx should not be None"
        self.controller.update_bbox(BboxUpdate(idx, class_name_new=dropdown_value_new))
        self.converter.refresh_figure_shapes(figure, self.controller.curr_bboxs)
        return AnnotateImageBboxsAIO.Update(no_update, figure, self._create_alert_layout())

    def _handle_new_box_drawn(self, relayout_data: Dict) -> Update:
        new_shape = relayout_data["shapes"][-1]
        new_bbox = self.converter.shape_to_bbox(new_shape)
        self.controller.add_bbox(new_bbox)
        return AnnotateImageBboxsAIO.Update(self._create_bbox_layout(), no_update, self._create_alert_layout())

    def _handle_box_updated(self, relayout_data: Dict) -> Update:

        # Parse shapes[0].x1 -> 0 from the brackets
        label = list(relayout_data.keys())[0]
        box_idx = int(label.split(".")[0].replace("shapes[","").replace("]",""))
        shapes_label = "shapes[%d]" % box_idx
        xyxy = [ relayout_data["%s.%s" % (shapes_label,label)] for label in ["x0","y0","x1","y1"] ]

        # Update
        update = BboxUpdate(box_idx, xyxy_new=xyxy)
        self.controller.update_bbox(update)
        return AnnotateImageBboxsAIO.Update(self._create_bbox_layout(), no_update, self._create_alert_layout())
        
class BboxToShapeConverter:

    def __init__(self, options: AnnotateImageOptions):
        options.check_valid()
        self.options = options

    def refresh_figure_shapes(self, figure: Dict, bboxs: Optional[List[Bbox]]):
        figure['layout']['shapes'] = self.bboxs_to_shapes(bboxs)

    def shape_to_bbox(self, shape: Dict) -> Bbox:
        xyxy: Xyxy = [ shape[c] for c in ["x0","y0","x1","y1"] ]
        return Bbox(xyxy, None)

    def bboxs_to_shapes(self, bboxs: Optional[List[Bbox]]) -> List[Dict]:
        if bboxs is None:
            return []
        return [ self.bbox_to_shape(bbox) for bbox in bboxs ]

    def bbox_to_shape(self, bbox: Bbox) -> Dict:
        # Line color
        if bbox.class_name is None:
            rgb = self.options.default_bbox_color
            if bbox.is_highlighted:
                rgb = (255,0,0)
        else:
            rgb = self.options.get_assign_color_for_class(bbox.class_name)
        line_color = 'rgba(%d,%d,%d,1)' % rgb

        # Fill color
        if bbox.is_highlighted:
            fill_color = 'rgba(%d,%d,%d,0.45)' % rgb
        else:
            fill_color = 'rgba(0,0,0,0)'

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
            'fillcolor': fill_color, 
            'fillrule': 'evenodd', 
            'type': 
            'rect', 
            'x0': bbox.xyxy[0], 
            'y0': bbox.xyxy[1], 
            'x1': bbox.xyxy[2], 
            'y1': bbox.xyxy[3]
            }
