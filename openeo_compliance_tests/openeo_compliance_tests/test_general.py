def test_capabilities(client, schema):
    response = client.get_json("/")
    schema.get_response_validator(path='/').validate(response)


def test_collections(client, schema):
    response = client.get_json("/collections")
    schema.get_response_validator(path='/collections').validate(response)


def test_collections_collection_id(client, schema, api_version):
    if '/collections/{collection_id}' in schema.get_paths():
        # Since 0.4.0
        path = '/collections/{collection_id}'
        field = 'id'
    else:
        # Old pre-0.4.0 style
        path = '/collections/{name}'
        field = 'name'
    validator = schema.get_response_validator(path=path)

    # TODO: handle this loop with pytest.mark.parametrize
    for collection in client.get_json('/collections')['collections']:
        response = client.get_json('/collections/{cid}'.format(cid=collection[field]))
        validator.validate(response)


def test_processes(client, schema):
    response = client.get_json('/processes')
    schema.get_response_validator(path='/processes').validate(response)


def test_output_formats(client, schema):
    response = client.get_json('/output_formats')
    schema.get_response_validator(path='/output_formats').validate(response)


def test_udf_runtimes(client, schema):
    response = client.get_json('/udf_runtimes')
    schema.get_response_validator(path='/udf_runtimes').validate(response)
