"""
MockAPI, a fully featured API/host routing framework for mitmproxy,
ease your life from if-else.

"""

import os
import sys
import traceback
import urllib.parse
from typing import List, Optional, Tuple, Union
from parse import Parser
from mitmproxy.http import HTTPFlow, HTTPResponse

import functools
import logging
import re

__author__ = "ttimasdf"
__copyright__ = "ttimasdf"
__license__ = "Apache-2.0"


class InterceptedAPI:
    REQUEST = 0x01
    RESPONSE = 0x02
    META_REQ_PASSTHROUGH = "mockapi-request-passthrough"
    META_RESP_PASSTHROUGH = "mockapi-response-passthrough"
    META_REQ_URLPARSE = "mockapi-request-urlparse"

    REGEX_HOST_HEADER = re.compile(r"^(?P<host>[^:]+|\[.+\])(?::(?P<port>\d+))?$")

    def __init__(self,
            default_host: Optional[str]=None,
            host_mapping: List[Tuple[Union[str, re.Pattern], str]]={},
            request_passthrough: bool=True,
            response_passthrough=True):

        self.default_host = default_host
        self.host_mapping = host_mapping
        self.request_routes: List[Tuple[Optional[str], Parser, callable]] = []
        self.response_routes: List[Tuple[Optional[str], Parser, callable]] = []
        self.request_passthrough = request_passthrough
        self.response_passthrough = response_passthrough

        self._log = logging.getLogger("MockAPI")
        if os.getenv("MOCKAPI_LOG_DEBUG"):
            self._log.setLevel(logging.DEBUG)
        self._log.info("%s started", self.__class__.__name__)

    def request(self, flow: HTTPFlow):
        if InterceptedAPI.META_REQ_URLPARSE in flow.metadata:
            url = flow.metadata[InterceptedAPI.META_REQ_URLPARSE]
        else:
            url = urllib.parse.urlparse(flow.request.path)
            flow.metadata[InterceptedAPI.META_REQ_URLPARSE] = url
        path = url.path
        if flow.metadata.get(InterceptedAPI.META_REQ_PASSTHROUGH) is True:
            self._log.warning("<= [%s] %s skipped because of previous passthrough", flow.request.method, path)
            return
        host = self.remap_host(flow)
        handler, params = self.find_handler(host, path, InterceptedAPI.REQUEST)
        if handler is not None:
            self._log.info("<= [%s] %s", flow.request.method, path)
            handler(flow, *params.fixed, **params.named)
        elif not self.request_passthrough:
            self._log.warning("<= [%s] %s default response", flow.request.method, path)
            flow.response = self.default_response()
        else:
            flow.metadata[InterceptedAPI.META_REQ_PASSTHROUGH] = True
            self._log.debug("<= [%s] %s passthrough", flow.request.method, path)

    def response(self, flow: HTTPFlow):
        if InterceptedAPI.META_REQ_URLPARSE in flow.metadata:
            url = flow.metadata[InterceptedAPI.META_REQ_URLPARSE]
        else:
            url = urllib.parse.urlparse(flow.request.path)
            flow.metadata[InterceptedAPI.META_REQ_URLPARSE] = url
        path = url.path
        if flow.metadata.get(InterceptedAPI.META_RESP_PASSTHROUGH) is True:
            self._log.warning("=> [%s] %s skipped because of previous passthrough", flow.response.status_code, path)
            return
        handler, params = self.find_handler(self.get_host(flow), path, InterceptedAPI.RESPONSE)
        if handler is not None:
            self._log.info("=> [%s] %s", flow.response.status_code, path)
            handler(flow, *params.fixed, **params.named)
        elif not self.response_passthrough:
            self._log.warning("=> [%s] %s default response", flow.response.status_code, path)
            flow.response = self.default_response()
        else:
            flow.metadata[InterceptedAPI.META_RESP_PASSTHROUGH] = True
            self._log.debug("=> [%s] %s passthrough", flow.response.status_code, path)

    def route(self, path, host=None, reqtype=REQUEST, catch_error=True):
        host = host or self.default_host

        # generic catch-all wrapper
        def catcher(func):
            @functools.wraps(func)
            def handler(flow: HTTPFlow, *args, **kwargs):
                try:
                    return func(flow, *args, **kwargs)
                except Exception as e:
                    etype, value, tback = sys.exc_info()
                    tb = "".join(traceback.format_exception(etype, value, tback))
                    self._log.error("Exception catched %s: %s", e.__class__.__name__, str(e))
                    self._log.error("Traceback:\n%s", tb)
                    flow.response = self.error_response(str(e))

            return handler

        def wrapper(handler):
            if catch_error:
                handler = catcher(handler)
            if reqtype == InterceptedAPI.REQUEST:
                self.request_routes.append((host, Parser(path), handler))
            elif reqtype == InterceptedAPI.RESPONSE:
                self.response_routes.append((host, Parser(path), handler))
            else:
                raise ValueError(f"Invalid route type: {reqtype}")
            return handler

        return wrapper

    def remap_host(self, flow: HTTPFlow, overwrite=True):
        host = self.get_host(flow)
        for src, dest in self.host_mapping:
            if isinstance(src, re.Pattern) and src.match(host):
                if overwrite:
                    flow.request.host = dest
                return dest
            elif isinstance(src, str) and host == src:
                if overwrite:
                    flow.request.host = dest
                return dest
        return host

    def get_host(self, flow: HTTPFlow) -> str:
        # Get Destination Host
        if flow.request.host_header is not None:
            m = self.REGEX_HOST_HEADER.match(flow.request.host_header)
            if m:
                return m.group("host").strip("[]")
        else:
            return flow.request.pretty_host

    def default_response(self):
        return HTTPResponse.make(404, "Not Found")

    def error_response(self, msg="APIServer Error"):
        return HTTPResponse.make(502, msg)

    def find_handler(self, host, path, reqtype=REQUEST):
        if reqtype == InterceptedAPI.REQUEST:
            routes = self.request_routes
        elif reqtype == InterceptedAPI.RESPONSE:
            routes = self.response_routes
        else:
            raise ValueError(f"Invalid route type: {reqtype}")

        for h, parser, handler in routes:
            if h is not None and h != host:
                continue
            parse_result = parser.parse(path)
            self._log.debug("Parse %s => %s", path, parse_result)
            if parse_result is not None:
                return handler, parse_result

        return None, None
