from .api_schema import collection_detail_schema, schema
import jsonschema


def test_describe_collection(backend):
    """
    Validates the detailed collections metadata document against the json schema.

    :param backend:
    :return:
    """

    max_collection = 10

    collections = backend.get_json("/collections")

    if "collections" in collections:

        for collection in collections["collections"]:
            if max_collection < 0:
                break
            if 'name' in collection:
                collection_detail = backend.get_json("/collections/{}".format(collection['name']))
                resolver = jsonschema.RefResolver.from_schema(schema)
                validator = jsonschema.validators.validator_for(schema)(collection_detail_schema, resolver=resolver)
                validator.validate(collection_detail, collection_detail_schema)
            max_collection -= 1