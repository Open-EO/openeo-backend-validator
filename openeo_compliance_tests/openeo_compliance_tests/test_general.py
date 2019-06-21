import _pytest.python
import pytest
import requests

from openeo_compliance_tests.helpers import ApiSchemaValidator, ApiClient, ResponseNotInSchema, get_api_version


@pytest.mark.parametrize("path", [
    '/',
    '/collections',
    '/processes',
    '/output_formats',
    '/udf_runtimes',
    '/service_types',
])
def test_get_generic(client: ApiClient, schema: ApiSchemaValidator, api_version: str, path: str):
    """
    Generic validation of simple get requests
    """
    response = client.get_json(path=path)
    try:
        validator = schema.get_response_validator(path=path)
    except ResponseNotInSchema:
        # Automatically skip paths that are not in tested API version (e.g. when validating against older schemas)
        pytest.skip('Path {p!r} not in schema version {v}'.format(p=path, v=api_version))
    validator.validate(response)


def test_collections_collection_id(client, schema):
    if '/collections/{collection_id}' in schema.get_paths():
        # Since 0.4.0
        path = '/collections/{collection_id}'
        field = 'id'
    else:
        # Old pre-0.4.0 style
        path = '/collections/{name}'
        field = 'name'
    validator = schema.get_response_validator(path=path)

    # TODO: handle this loop with pytest.mark.parametrize?
    # TODO: limit the number of collections to check?
    for collection in client.get_json('/collections')['collections']:
        response = client.get_json('/collections/{cid}'.format(cid=collection[field]))
        validator.validate(response)


def test_get_unauthorized(client: ApiClient, unauthorized_get_path: str):
    """
    Check that paths that require authentication indeed return with a 4XX HTTP code
    """
    response = client.get(unauthorized_get_path)
    if response.status_code == requests.codes.not_found:
        pytest.skip('{p} not found'.format(p=unauthorized_get_path))
    assert response.status_code in (
        requests.codes.unauthorized,  # HTTP status code 401
        requests.codes.forbidden,  # HTTP status code 403
        requests.codes.not_allowed,  # HTTP status code 405
    )


def pytest_generate_tests(metafunc: _pytest.python.Metafunc):
    """
    Pytest hook for custom test parametrization
    """
    if 'unauthorized_get_path' in metafunc.fixturenames:
        schema = ApiSchemaValidator.from_version(get_api_version(metafunc.config))
        # Search for get requests which require authentication
        paths = []
        for path in schema.get_paths():
            if '{' not in path:
                path_get_schema = schema.get_path_schema(path).get('get', {})
                if 'security' in path_get_schema and all(s != {} for s in path_get_schema['security']):
                    paths.append(path)
        metafunc.parametrize('unauthorized_get_path', paths)
