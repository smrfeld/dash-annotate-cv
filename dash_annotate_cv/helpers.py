import dash
import json
import logging
from typing import Tuple, Optional, List, Union


logger = logging.getLogger(__name__)


Xyxy = List[Union[float,int]]
Xywh = List[Union[float,int]]


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
