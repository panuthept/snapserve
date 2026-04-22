import pickle
import base64
from typing import Any
from httpx import Client


def set_remote_attribute(client: Client, context_id: str, name: str, path: list, value: Any):
    # Type consistency check can be added here by fetching the current value and comparing types before setting the new value
    response = client.get(
        context_id=context_id,
        attr_name=name,
        attr_path=path,
    )
    remote_type = response["type"]
    if remote_type != "variable":
        raise TypeError(f"Only variables can be mutated on the remote server. Attempting to mutate a remote attribute of type '{remote_type}'.")
    if str(type(value)) != str(type(response["value"])):
        raise TypeError(f"Type mismatch when setting remote attribute '{name}'. Expected type '{type(response['value']).__name__}', got type '{type(value).__name__}'.")
    
    # Type check to see if the value is JSON serializable, if not, use pickle to serialize it and send it as a string
    if isinstance(value, (int, float, str, bool, list, dict, type(None))):
        value = {"value": value}
    else:
        value = {"encoded_value": base64.b64encode(pickle.dumps(value)).decode("ascii")}
    
    # Finally, send the PUT request to update the value on the remote server
    client.put(
        context_id=context_id,
        attr_name=name,
        attr_path=path,
        **value
    )