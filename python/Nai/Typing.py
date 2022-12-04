from typing import TypedDict, Dict, Any

class RequestHeader(TypedDict, total=False):
    Authorization: str

class Request(TypedDict, total=False):
    headers: RequestHeader
    json: Dict
    data: Dict[str, Any]
