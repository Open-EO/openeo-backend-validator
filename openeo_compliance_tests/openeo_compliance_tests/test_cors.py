"""

Tests for handling of Cross-Origin Resource Sharing (CORS)
https://open-eo.github.io/openeo-api/cors/

"""
import pytest
import requests

from openeo_compliance_tests.helpers import ApiClient


def csv_to_list(s: str):
    """Parse comma-separated list (and make lowercase)"""
    return [x.lower().strip() for x in s.split(',')]


@pytest.mark.parametrize("path", [
    '/',
    '/collections',
    '/processes'
    # TODO: more endpoints?
])
def test_options_request(client: ApiClient, path: str):
    origin = 'http://example.com'
    r = client.request(method='options', path=path, expect_status_code = 204, headers={'Origin': origin})

    assert r.status_code == 204

    # Note: r.headers is CaseInsensitiveDict
    assert r.headers['access-control-allow-origin'] == origin

    # TODO test Access-Control-Allow-Credentials (depends on whether backend supports authentication)

    assert 'content-type' in csv_to_list(r.headers['access-control-allow-headers'])

    # TODO: check more methods?
    assert 'get' in csv_to_list(r.headers['access-control-allow-methods'])

    expose_headers = set(csv_to_list(r.headers['access-control-expose-headers']))
    assert {'location', 'openeo-identifier', 'openeo-costs'}.issubset(expose_headers)

    # This header SHOULD be available, but it is not mandatory. So don't fail if it doesn't exist.
    # assert r.headers['content-type'] == 'application/json'
