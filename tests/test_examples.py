import importlib.machinery
import importlib.util
import os
import re
import sys

import pytest
from mitmproxy.http import Response
from mitmproxy.test import taddons, tflow

__author__ = "ttimasdf"
__copyright__ = "ttimasdf"
__license__ = "Apache-2.0"


@pytest.mark.parametrize(
    "script_path",
    [
        "examples/httpbin/httpbin.py",
        "examples/krisp/krisp.py",
        "examples/polyv_scrapper/polyv.py",
    ],
)
def test_scripts_import(script_path):
    """
    Modified mirmproxy.addons.script.load_script, without catching exceptions.
    Use this test to check whether an example script is importable.
    Original version will silently catch every exception,
    not suitable for unit testing.
    """

    fullname = "__mitmproxy_script__.{}".format(
        os.path.splitext(os.path.basename(script_path))[0]
    )
    # the fullname is not unique among scripts, so if there already is an existing script with said
    # fullname, remove it.
    sys.modules.pop(fullname, None)
    sys.path.insert(0, os.path.dirname(script_path))
    m = None
    loader = importlib.machinery.SourceFileLoader(fullname, script_path)
    spec = importlib.util.spec_from_loader(fullname, loader=loader)
    assert spec
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    if not getattr(m, "name", None):
        m.name = script_path

    assert len(m.addons) > 0


class TestScripts:
    def test_httpbin(self, tdata, toptions):
        with taddons.context(options=toptions) as tctx:
            s = tctx.script(tdata.path("../examples/httpbin/httpbin.py"))
            api = s.addons[0]

            flow = tflow.tflow()
            flow.request.url = "http://httpbin.org/get"
            assert flow.response is None

            api.request(flow)
            assert flow.request.query["payload"] == "evil_param"

    def test_krisp_forward(self, tdata, toptions):
        with taddons.context(options=toptions) as tctx:
            s = tctx.script(tdata.path("../examples/krisp/krisp.py"))
            api = s.addons[0]

            flow = tflow.tflow()
            flow.request.url = "https://api.krisp.ai/random-path"
            assert flow.response is None

            api.request(flow)
            assert re.match(
                r"\d+\.\d+\.\d+\.\d+", flow.request.headers["X-Forwarded-For"]
            )

    def test_krisp_analytics(self, tdata, toptions):
        with taddons.context(options=toptions) as tctx:
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
    def test_polyv(self, capsys, monkeypatch, tdata, toptions, url, resp, stdout):
        with taddons.context(options=toptions) as tctx:
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
                import base64
                import json

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
