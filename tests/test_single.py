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

    @api.route(
        "/{}/{}/{vid}_1.m3u8",
        "hls.videocc.net",
    )
    def route2(flow: HTTPFlow, *args, vid):
        flow.response = Response.make(200, "TEST 2 INTERCEPTED")

    return api


@pytest.mark.parametrize(
    "req_url,resp_body",
    [
        ("http://example.com/test", "TEST intercepted"),
        ("http://hls.videocc.net/jkag324wd2/e/cwqzcxkvj0iukomqxu0l591u2dke4vkc_1.m3u8", "TEST 2 INTERCEPTED"),
    ],
)
def test_intercepted_route(api_simple, req_url, resp_body):
    with taddons.context(api_simple) as tctx:
        flow = tflow.tflow()
        flow.request.url = req_url
        assert flow.response is None

        api_simple.request(flow)
        assert resp_body in flow.response.text


def test_non_intercepted_route(api_simple):
    with taddons.context(api_simple) as tctx:
        flow = tflow.tflow()
        flow.request.path = "/test2"
        assert flow.response is None

        api_simple.request(flow)
        assert flow.response is None
