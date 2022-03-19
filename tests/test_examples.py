import re
import pytest
from mitmproxy.http import Response
from mitmproxy.test import taddons, tflow

from .tserver import MasterTest

__author__ = "ttimasdf"
__copyright__ = "ttimasdf"
__license__ = "Apache-2.0"


class TestScripts(MasterTest):
    def test_httpbin(self, tdata):
        with taddons.context() as tctx:
            s = tctx.script(tdata.path("../examples/httpbin/httpbin.py"))
            api = s.addons[0]

            flow = tflow.tflow()
            flow.request.url = "http://httpbin.org/get"
            assert flow.response is None

            api.request(flow)
            assert flow.request.query["payload"] == "evil_param"

    def test_krisp_forward(self, tdata):
        with taddons.context() as tctx:
            s = tctx.script(tdata.path("../examples/krisp/krisp.py"))
            api = s.addons[0]

            flow = tflow.tflow()
            flow.request.url = "https://api.krisp.ai/random-path"
            assert flow.response is None

            api.request(flow)
            assert re.match(
                r"\d+\.\d+\.\d+\.\d+", flow.request.headers["X-Forwarded-For"]
            )

    def test_krisp_analytics(self, tdata):
        with taddons.context() as tctx:
            s = tctx.script(tdata.path("../examples/krisp/krisp.py"))
            api = s.addons[0]

            flow = tflow.tflow()
            flow.request.url = "https://analytics.krisp.ai/random-path-as-well"
            flow.request.set_content(rb'{"krisp": "analytics"}')
            assert flow.response is None

            api.request(flow)
            assert flow.response.headers["Content-Type"] == "application/json"

            payload = flow.response.json()
            assert payload["message"] == "Success"
            assert payload["data"]["app"]["krisp"] == "analytics"

    @pytest.mark.parametrize(
        "url,resp,stdout",
        [
            ("http://example.com/test", b"", ""),  # Nonsense url, should return nothing
            (  # step1
                f"http://player.polyv.net/videojson/cwqzcxkvj0iukomqxu0l591u2dke4vkc_c.json",
                b'{"body": "deadbeef"}',
                "Decrypted videojson for Test Lesson Title",
            ),
            (  # step2
                f"http://hls.videocc.net/jkag324wd2/e/cwqzcxkvj0iukomqxu0l591u2dke4vkc_1.m3u8?pid=544927262345396034173&device=desktop",
                b"",
                f"Found playlist for 123456 Test Lesson Title",
            ),
            (  # step3
                f"http://hls.videocc.net/playsafe/jkag324wd2/e/cwqzcxkvj0iukomqxu0l591u2dke4vkc_1.key?pid=544927262345396034173&device=desktop",
                b"",
                f"Found key for 123456 Test Lesson Title",
            ),
        ],
    )
    def test_polyv(self, capsys, monkeypatch, tdata, url, resp, stdout):
        with taddons.context() as tctx:
            polyv = tctx.script(tdata.path("../examples/polyv_scrapper/polyv.py"))
            api = polyv.addons[0]

            # Add test data
            polyv.ctx.lessons["cwqzcxkvj0iukomqxu0l591u2dke4vkc"] = polyv.Lesson(
                "cwqzcxkvj0iukomqxu0l591u2dke4vkc",
                "Test Lesson Title",
                "test/category",
                123456,
                1,
            )

            def monkey_decrypt(*args):
                import json
                import base64

                payload = {polyv.REDACTED_CONSTANT: "whosyourdaddy"}
                return base64.b64encode(json.dumps(payload).encode())

            def monkey_process_lesson(lesson):
                print("process_lesson is running")

            monkeypatch.setattr(polyv, "decrypt", monkey_decrypt)
            monkeypatch.setattr(polyv, "process_lesson", monkey_process_lesson)

            flow = tflow.tflow()
            flow.request.url = url
            flow.response = Response.make(content=resp)

            api.response(flow)
            captured = capsys.readouterr()
            assert stdout in captured.out
