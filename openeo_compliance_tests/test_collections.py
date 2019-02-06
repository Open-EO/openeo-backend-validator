from .api_schema import collections_schema, schema
import jsonschema

def test_collections(backend):
    """
    Validates the collections metadata document against the json schema.

    :param backend:
    :return:
    """

    collections = backend.get_json("/collections")
    resolver = jsonschema.RefResolver.from_schema(schema)
    validator = jsonschema.validators.validator_for(schema)(collections_schema,resolver=resolver)
    validator.validate(collections,collections_schema)


