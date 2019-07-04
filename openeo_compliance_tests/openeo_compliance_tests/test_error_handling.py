"""

https://open-eo.github.io/openeo-api/errors/

"""

import _pytest.python
import pytest
import requests

from openeo_compliance_tests.helpers import ApiClient, get_api_version, OpenApiSpec


def pytest_generate_tests(metafunc: _pytest.python.Metafunc):
    """
    Pytest hook for custom test parametrization
    """
    if 'unauthorized_get_path' in metafunc.fixturenames:
        spec = OpenApiSpec.from_version(get_api_version(metafunc.config))
        # Search for get requests which require authentication
        paths = []
        for path in spec.get_paths():
            if '{' not in path:
                path_get_schema = spec.get_path_schema(path).get('get', {})
                if 'security' in path_get_schema and all(s != {} for s in path_get_schema['security']):
                    paths.append(path)
        metafunc.parametrize('unauthorized_get_path', paths)


def test_get_unauthorized(client: ApiClient, unauthorized_get_path: str):
    """
    Check that paths that require authentication indeed return with a 401 Unauthorized HTTP code

    https://open-eo.github.io/openeo-api/errors/#account_management
    """
    response = client.get(unauthorized_get_path)
    if response.status_code == requests.codes.not_found:
        pytest.skip('{p} not found'.format(p=unauthorized_get_path))
    assert response.status_code == requests.codes.unauthorized


@pytest.mark.parametrize(['path', 'http_code', 'error_code'], [
    ('/invalid/path/to/nowhere', requests.codes.not_found, 'NotFound'),
    ('/collections/invalid-collection-name-foobar', requests.codes.not_found, 'CollectionNotFound'),
])
def test_invalid_path(client: ApiClient, path: str, http_code: int, error_code: str):
    """Test GET request to invalid path"""
    r = client.get(path=path)
    assert r.status_code == http_code
    error = r.json()
    assert isinstance(error, dict)
    assert 'code' in error
    assert error['code'] == error_code
    assert 'message' in error
