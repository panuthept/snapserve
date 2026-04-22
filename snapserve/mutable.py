from typing import Any
from snapserve.remote import _RemoteAttribute, Remote
from snapserve.utils.attribute import set_remote_attribute


class Mutable:
    def __init__(self, remote: Remote):
        self._remote = remote
        self._client = remote._client
        self._context_id = remote._context_id

    def __getattr__(self, name: str) -> Any:
        attr = self._remote.__getattr__(name) # Delegate attribute access to the Remote instance
        if isinstance(attr, _RemoteAttribute):
            attr._mutable = True # Mark the attribute as mutable so that it can be set later
        return attr

    def __setattr__(self, name: str, value: Any):
        if name in {"_remote", "_client", "_context_id"}:
            super().__setattr__(name, value)
            return
        set_remote_attribute(self._client, self._context_id, name, [], value)