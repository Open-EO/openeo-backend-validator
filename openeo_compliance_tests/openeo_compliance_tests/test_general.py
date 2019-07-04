import pytest

from openeo_compliance_tests.helpers import ApiSchemaValidator, ApiClient, ResponseNotInSchema


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
    try:
        validator = schema.get_response_validator(path=path)
    except ResponseNotInSchema:
        # Automatically skip paths that are not in tested API version (e.g. when validating against older schemas)
        pytest.skip('Path {p!r} not in schema version {v}'.format(p=path, v=api_version))
    else:
        response = client.get_json(path=path)
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


def test_well_known_openeo(client, schema, api_version):
    # Special case: /.well-known/openeo should be available directly under domain
    path = '/.well-known/openeo'
    client = ApiClient(backend=client.domain)
    test_get_generic(client=client, schema=schema, api_version=api_version, path=path)

