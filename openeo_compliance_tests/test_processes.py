from .api_schema import processes_schema,schema
import jsonschema

def test_processes(backend):
    """
    Validates the processes metadata document against the json schema.

    :param backend:
    :return:
    """

    processes = backend.get_json("/processes")
    resolver = jsonschema.RefResolver.from_schema(schema)
    validator = jsonschema.validators.validator_for(schema)(processes_schema,resolver=resolver)
    validator.validate(processes,processes_schema)
