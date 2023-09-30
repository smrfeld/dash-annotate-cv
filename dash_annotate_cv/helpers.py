import dash
import json
import logging


logger = logging.getLogger(__name__)


def get_trigger_id() -> str:
    """Get the trigger ID from the callback context
    """
    ctx = dash.callback_context
    logger.debug(f"ctx.triggered: {ctx.triggered}")
    # ctx.triggered = [{'prop_id': '<ID>.n_clicks', 'value': 1}]
    # Extract ID
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    #if trigger_id != "":
    #    trigger_id = json.loads(trigger_id)["subcomponent"]
    return trigger_id
