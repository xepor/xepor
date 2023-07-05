# Changelog

% **Note**: This document contains some [MyST](https://myst-parser.readthedocs.io/en/latest/index.html) syntax which is not completely Markdown. For better experience (and cross references to the changed code) you could read this document on [Read the Docs](https://xepor.readthedocs.io/en/latest/changelog.html)
## Version 0.5.1

- Feature: Add compatibility with mitmproxy 9.x and Python 3.11~3.12.
  - Since mitmproxy 8.x is not compatible with Python 3.11, therefore updating to mitmproxy 9.x + xepor 0.5.1 is recommended especially for Kali users with rolling updates.

## Version 0.5.0

**⚠️Breaking Change⚠️**: Incompatible API changes.

- Change: Move some constants inside {class}`~xepor.InterceptedAPI` to seperate enums: {func}`xepor.RouteType`, {func}`xepor.FlowMeta`. ([xepor/xepor@83128e8](https://github.com/xepor/xepor/commit/83128e81f8c181cd23363d27c76209b9de1c49eb))
- Change: rename `reqtype` in {func}`xepor.InterceptedAPI.route` to `rtype`. The name there before is for historical reason. [xepor/xepor@c6c7e83](https://github.com/xepor/xepor/commit/c6c7e8319aef95de01a0f797d9bb2c01632b7609)
- All exposed API is now type hinted and well documented! check the latest [Documentation](https://xepor.readthedocs.io/en/latest). example scripts are also updated with API change.

## Version 0.4.0

- Feature: Add compatibility with mitmproxy 8.x.

## Version 0.3.0

- Feature: Add `return_error` option for {func}`xepor.InterceptedAPI.route` ([xepor/xepor@fddad13](https://github.com/xepor/xepor/commit/fddad13efc0ed08b214c4f4078e130b04deeeab0))
- Add more docs and examples. Also some tests to ensure the script stay up-to-date with version changes. ([xepor/xepor@3f96bf1](https://github.com/xepor/xepor/commit/3f96bf16b8d45b9fb49485abd475b7139422e1b9))

## Version 0.2.0

**⚠️Breaking Change⚠️**: mitmproxy 7.0 contains backward-incompatible API change comparing with <=6.x, update to 7.x may need to modify all of your scripts (including those not written with Xepor). Just a change on some methods' signatures.

- Feature: Add `blacklist_domain` and `respect_proxy_headers` options for {class}`~xepor.InterceptedAPI`. Refer to [API Doc](https://xepor.readthedocs.io/en/latest/api/modules.html#xepor.InterceptedAPI) for their usage. ([xepor/xepor@aa2517d](https://github.com/xepor/xepor/commit/aa2517d65f800944587a25678b1e624f84bdf13f))
- Feature: Add a debug header when client request hitting {func}`~xepor.InterceptedAPI.default_response` ([xepor/xepor@d57be79](https://github.com/xepor/xepor/commit/d57be794a2e8863bc8aebec070f4a78be8ec121b))
- Fix: adopt API change in mitmproxy 7.x ([xepor/xepor@beedeab](https://github.com/xepor/xepor/commit/beedeab446508bf0df82c90e05d99b5da9ee3753))
- Fix: Request is forwarded to wrong destination host when mitmproxy is start in reverse/upstream mode. ([xepor/xepor@aa2517d](https://github.com/xepor/xepor/commit/aa2517d65f800944587a25678b1e624f84bdf13f)) **Be sure to start mitmproxy with `--set connection_strategy=lazy` under ANY circumstances or the upstream connection may still be wrong.**
- Update example scripts.

## Version 0.1 (development)

This is **the only version** compatible with mitmproxy <= 6.x

- Implement most features.
