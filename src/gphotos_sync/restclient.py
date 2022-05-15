import logging
from json import dumps
from typing import Any, Dict, List, Union

from requests import Session
from requests.exceptions import HTTPError

JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONType = Union[Dict[str, JSONValue], List[JSONValue]]

log = logging.getLogger(__name__)

"""
Defines very simple classes to create a callable interface to a REST api
from a discovery REST description document.

Intended as a super simple replacement for google-api-python-client, using
requests instead of httplib2

giles 2018
"""


# a dummy decorator to suppress unresolved references on this dynamic class
def dynamic_attrs(cls):
    return cls


@dynamic_attrs
class RestClient:
    """
    To create a callable client to a REST API, instantiate this class.
    For details of the discovery API see:
        https://developers.google.com/discovery/v1/using
    """

    def __init__(self, api_url: str, auth_session: Session):
        """
        Create a rest API object tree from an api description
        """
        self.auth_session: Session = auth_session
        service_document = self.auth_session.get(api_url).json()
        self.json: JSONType = service_document
        self.base_url: str = str(service_document["baseUrl"])
        for c_name, collection in service_document["resources"].items():
            new_collection = Collection(c_name)
            setattr(self, c_name, new_collection)
            for m_name, method in collection["methods"].items():
                new_method = Method(self, **method)
                setattr(new_collection, m_name, new_method)


# pylint: disable=no-member
class Method:
    """ Represents a method in the REST API. To be called using its execute
    method, the execute method takes a single parameter for body and then
    named parameters for Http Request parameters.

    e.g.
        api = RestClient(https://photoslibrary.googleapis.com/$discovery' \
                             '/rest?version=v1', authenticated_session)
        api.albums.list.execute(pageSize=50)
    """

    def __init__(self, service: RestClient, **k_args: Dict[str, str]):
        self.path: str = ""
        self.httpMethod: str = ""
        self.service: RestClient = service
        self.__dict__.update(k_args)
        self.path_args: List[str] = []
        self.query_args: List[str] = []
        if hasattr(self, "parameters"):
            for key, value in self.parameters.items():  # type: ignore
                if value["location"] == "path":
                    self.path_args.append(key)
                else:
                    self.query_args.append(key)

    def execute(self, body: str = "", **k_args: Dict[str, str]):
        """executes the remote REST call for this Method"""
        path_args: Dict[str, Dict] = {
            k: k_args[k] for k in self.path_args if k in k_args
        }
        query_args: Dict[str, Dict] = {
            k: k_args[k] for k in self.query_args if k in k_args
        }
        path: str = self.service.base_url + self.make_path(path_args)
        if body:
            body = dumps(body)

        log.trace(  # type: ignore
            "\nREQUEST: %s to %s params=%s\n%s",
            self.httpMethod,
            path,
            query_args,
            body,
        )
        result = self.service.auth_session.request(
            self.httpMethod, data=body, url=path, timeout=10, params=query_args
        )
        log.trace(  # type: ignore
            "\nRESPONSE: %s\n%s", result.status_code, str(result.content)
        )

        try:
            result.raise_for_status()
        except HTTPError:
            log.error(
                "Request failed with status {}: {}".format(
                    result.status_code, str(result.content)
                )
            )
            raise
        return result

    def make_path(self, path_args: Dict[str, Any]) -> str:
        """Extracts the arguments from path_args and inserts them into
        the URL template defined in self.path

        Returns:
            The URL with inserted parameters
        """
        result = str(self.path)
        path_params = []
        for key, value in path_args.items():
            path_param = "{{+{}}}".format(key)
            if path_param in result:
                result = result.replace("{{+{}}}".format(key), value)
                path_params.append(key)
        for key in path_params:
            path_args.pop(key)
        return result


class Collection:
    """Used to represent a collection of methods
    e.g. Google Photos API - mediaItems"""

    def __init__(self, name: str):
        self.collection_name = name
