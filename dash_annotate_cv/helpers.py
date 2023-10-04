import dash
import json
import logging
from typing import Tuple, Optional, List, Union


logger = logging.getLogger(__name__)


Xyxy = List[Union[float,int]]
Xywh = List[Union[float,int]]


def xyxy_to_xywh(xyxy: Xyxy) -> Xywh:
    """Convert xyxy to xywh
    """
    return [ min(xyxy[0],xyxy[2]), min(xyxy[1],xyxy[3]), abs(xyxy[2] - xyxy[0]), abs(xyxy[3] - xyxy[1])]


def xywh_to_xyxy(xywh: Xywh) -> Xyxy:
    """Convert xywh to xyxy
    """
    return [xywh[0], xywh[1], xywh[0] + xywh[2], xywh[1] + xywh[3]]


class UnknownError(Exception):
    pass


def get_trigger_id() -> Tuple[str,Optional[int]]:
    """Get the trigger ID from the callback context
    """
    ctx = dash.callback_context
    
    # ctx.triggered = [{'prop_id': '<ID>.n_clicks', 'value': 1}]
    # Extract ID
    logger.debug(f"ctx.triggered = {ctx.triggered}")
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    idx: Optional[int] = None

    try:
        # Possibly extract the subcomponent if AIO involved
        if trigger_id != "":
            data = json.loads(trigger_id)
            trigger_id = data["subcomponent"]
            idx = data["idx"]
    except:
        pass
    return trigger_id, idx
