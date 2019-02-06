from .api_schema import capabilities_schema
import jsonschema

def test_capabilities(backend):
    """
    Validates the backend capabilities document against the json schema.

    :param backend:
    :return:
    """

    capabilities = backend.get_json("")
    jsonschema.validate(capabilities, capabilities_schema)
