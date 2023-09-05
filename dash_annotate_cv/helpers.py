import dash
import json

def get_trigger_id() -> str:
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id != "":
        trigger_id = json.loads(trigger_id)["subcomponent"]
    return trigger_id
