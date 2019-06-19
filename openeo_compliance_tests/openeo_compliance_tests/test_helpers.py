import jsonschema
import pytest

from openeo_compliance_tests.helpers import ApiSchemaValidator

SIMPLE_SCHEMA = {
    "openapi": "3.0.2",
    "info": {
        "title": "Simple API",
        "version": "1.2.3"
    },
    "paths": {
        "/helloworld": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Computer says hello world",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": [
                                        "greeting",
                                    ],
                                    "properties": {
                                        "greeting": {
                                            "type": "string",
                                        },
                                        "subject": {
                                            "type": "string",
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


def test_api_schema_validator():
    schema = ApiSchemaValidator(SIMPLE_SCHEMA)
    validator = schema.get_response_validator(path='/helloworld')
    validator.validate({'greeting': 'hello', 'subject': 'world'})
    validator.validate({'greeting': 'hello'})
    with pytest.raises(jsonschema.ValidationError, match="'greeting' is a required property"):
        validator.validate({})


def test_api_schema_validator_wrong_path():
    schema = ApiSchemaValidator(SIMPLE_SCHEMA)
    with pytest.raises(KeyError):
        schema.get_response_validator(path='/foobar')
