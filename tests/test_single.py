import pytest
from mitmproxy.http import HTTPFlow, Response
from mitmproxy.test import taddons, tflow
from xepor import InterceptedAPI


__author__ = "ttimasdf"
__copyright__ = "ttimasdf"
__license__ = "Apache-2.0"


@pytest.fixture
def api_simple():
    api = InterceptedAPI("example.com")

    @api.route("/test")
    def route1(flow: HTTPFlow):
        flow.response = Response.make(200, "TEST intercepted")

    return api


def test_intercepted_route(api_simple):
    with taddons.context(api_simple) as tctx:
        flow = tflow.tflow()
        flow.request.host = "example.com"
        flow.request.path = "/test"
        assert flow.response is None

        api_simple.request(flow)
        assert "TEST intercepted" in flow.response.text


def test_non_intercepted_route(api_simple):
    with taddons.context(api_simple) as tctx:
        flow = tflow.tflow()
        flow.request.path = "/test2"
        assert flow.response is None

        api_simple.request(flow)
        assert flow.response is None
