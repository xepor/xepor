[![Unit Tests](https://github.com/xepor/xepor/actions/workflows/test.yml/badge.svg)](https://github.com/xepor/xepor/actions/workflows/test.yml)
[![PyPI-Server](https://img.shields.io/pypi/v/xepor.svg)](https://pypi.org/project/xepor/)
![PyPI - Status](https://img.shields.io/pypi/status/xepor)
[![Documentation Status](https://readthedocs.org/projects/xepor/badge/?version=latest)](https://xepor.readthedocs.io/en/latest/?badge=latest)
[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)
[![996.icu](https://img.shields.io/badge/link-996.icu-red.svg)](https://996.icu)

# Xepor

[Xepor](https://github.com/xepor/xepor) (pronounced */ˈzɛfə/*, zephyr), a web routing framework for reverse engineers and security researchers.
It provides a Flask-like API for hackers to intercept and modify HTTP request and/or HTTP response in a human-friendly coding style.

This project is meant to be used with [mitmproxy](https://github.com/mitmproxy/mitmproxy/). User write scripts with `xepor`, and run the script *inside* mitmproxy with `mitmproxy -s your-script.py`.

If you want to step from PoC to production, from demo(e.g. [http-reply-from-proxy.py](https://github.com/mitmproxy/mitmproxy/blob/v7.0.4/examples/addons/http-reply-from-proxy.py), [http-trailers.py](https://github.com/mitmproxy/mitmproxy/blob/v7.0.4/examples/addons/http-trailers.py), [http-stream-modify.py](https://github.com/mitmproxy/mitmproxy/blob/v7.0.4/examples/addons/http-stream-modify.py)) to something you could take out with your WiFi Pineapple, then Xepor is for you!

## Features

1. Code everything with `@api.route()`, just like Flask! Write everything in *one* script and no `if..else` any more.
2. Handle multiple URL routes, even multiple hosts in one `InterceptedAPI` instance.
3. For each route, you can choose to modify the request *before* connecting to server (or even return a fake response without connection to upstream), or modify the response *before* forwarding to user.
4. Blacklist mode or whitelist mode. Only allow URL endpoints defined in scripts to connect to upstream, blocking everything else (in specific domain) with HTTP 404. Suitable for transparent proxying.
5. Human readable URL path definition and matching powered by [parse](https://pypi.org/project/parse/)
6. Host remapping. define rules to redirect to genuine upstream from your fake hosts. Regex matching is supported. **Best for SSL stripping and server side license cracking**!
7. Plus all the bests from [mitmproxy](https://github.com/mitmproxy/mitmproxy/)! **ALL** operation modes ( `mitmproxy` / `mitmweb` + `regular` / `transparent`  / `socks5` / `reverse:SPEC` / `upstream:SPEC`) are fully supported.

## Use Case

1. Evil AP and phishing through MITM.
2. Sniffing traffic from specific device by iptables + transparent proxy, modify the payload with xepor on the fly.
3. Cracking cloud based software license. See [examples/krisp/](https://github.com/xepor/xepor-examples/tree/main/krisp/) as an example.
4. Write complicated web crawler in **\~100 lines of codes**. See [examples/polyv_scrapper/](https://github.com/xepor/xepor-examples/tree/main/polyv_scrapper/) as an example.
5. ... and many more.

SSL stripping is NOT provided by this project.

# Installation

```bash
pip install xepor
```

# Quick start

Take the script from [examples/httpbin](https://github.com/xepor/xepor-examples/tree/main/httpbin/) as an example.

```bash
mitmweb --web-host=\* --set connection_strategy=lazy -s example/httpbin/httpbin.py
```

In this example, we setup the mitmproxy server on `127.0.0.1`. You could change it to any IP on your machine or alternatively to the IP of your VPS. The mitmproxy server running in reverse, upstream and transparent mode requires `--set connection_strategy=lazy` option to be set so that Xepor could function correctly. I recommand this option always be on for best stability.

Set your Browser HTTP Proxy to `http://127.0.0.1:8080`, and access web interface at http://127.0.0.1:8081/.

Send a GET request from http://httpbin.org/#/HTTP_Methods/get_get , Then you could see the modification made by Xepor in mitmweb interface, browser devtools or Wireshark.

The `httpbin.py` do two things.

1. When user access http://httpbin.org/get, inject a query string parameter `payload=evil_param` inside HTTP request.
2. When user access http://httpbin.org/basic-auth/xx/xx/ (we just pretends we don't know the password), sniff `Authorization` headers from HTTP requests and print the password to the attacker.

Just what mitmproxy always do, but with code written in [*xepor*](https://github.com/xepor/xepor) way.

```python
# https://github.com/xepor/xepor-examples/tree/main/httpbin/httpbin.py
from mitmproxy.http import HTTPFlow
from xepor import InterceptedAPI, RouteType


HOST_HTTPBIN = "httpbin.org"

api = InterceptedAPI(HOST_HTTPBIN)


@api.route("/get")
def change_your_request(flow: HTTPFlow):
    """
    Modify URL query param.
    Test at:
    http://httpbin.org/#/HTTP_Methods/get_get
    """
    flow.request.query["payload"] = "evil_param"


@api.route("/basic-auth/{usr}/{pwd}", rtype=RouteType.RESPONSE)
def capture_auth(flow: HTTPFlow, usr=None, pwd=None):
    """
    Sniffing password.
    Test at:
    http://httpbin.org/#/Auth/get_basic_auth__user___passwd_
    """
    print(
        f"auth @ {usr} + {pwd}:",
        f"Captured {'successful' if flow.response.status_code < 300 else 'unsuccessful'} login:",
        flow.request.headers.get("Authorization", ""),
    )


addons = [api]
```
