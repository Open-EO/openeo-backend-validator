import pytest

from openeo_compliance_tests.helpers import ApiClient, ResponseNotInSchema, OpenApiValidator, OpenApiSpec


@pytest.mark.parametrize("path", [
    '/',
    '/collections',
    '/processes',
    '/output_formats',
    '/udf_runtimes',
    '/service_types',
])
def test_get_generic(client: ApiClient, validator: OpenApiValidator, api_version: str, path: str):
    """
    Generic validation of simple get requests
    """
    try:
        response = client.get(path=path, expect_status_code=200)
        validator.validate_response(path=path, response=response, method='get')
    except ResponseNotInSchema:
        # Automatically skip paths that are not in tested API version (e.g. when validating against older schemas)
        pytest.skip('Path {p!r} not in schema version {v}'.format(p=path, v=api_version))


def test_collections_collection_id(client: ApiClient, spec: OpenApiSpec, validator: OpenApiValidator):
    if '/collections/{collection_id}' in spec.get_paths():
        # Since 0.4.0
        path = '/collections/{collection_id}'
        field = 'id'
    else:
        # Old pre-0.4.0 style
        path = '/collections/{name}'
        field = 'name'

    # TODO: handle this loop with pytest.mark.parametrize?
    # TODO: option to limit the number of collections to check?
    for collection in client.get('/collections').json()['collections'][:10]:
        response = client.get('/collections/{cid}'.format(cid=collection[field]))
        validator.validate_response(path=path, response=response, method='get')


def test_well_known_openeo(client, validator, api_version):
    # Special case: /.well-known/openeo should be available directly under domain
    path = '/.well-known/openeo'
    client = ApiClient(backend=client.domain)
    test_get_generic(client=client, validator=validator, api_version=api_version, path=path)
