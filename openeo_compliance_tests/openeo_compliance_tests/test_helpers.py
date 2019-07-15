import contextlib
import json
import pathlib
from typing import Union

import jsonschema
import pytest
from requests import Response

from openeo_compliance_tests.helpers import OpenApiSpec, PurePythonValidator, ResponseNotInSchema, Capabilities

TEST_SCHEMA = {
    "openapi": "3.0.2",
    "info": {
        "title": "Simple API",
        "version": "1.2.3"
    },
    "paths": {
        "/helloworld": {"get": {"responses": {"200": {
            "description": "Computer says hello world",
            "content": {"application/json": {
                "schema": {
                    "type": "object",
                    "required": ["greeting"],
                    "properties": {
                        "greeting": {"type": "string"},
                        "subject": {"type": "string"}
                    }
                }
            }}
        }}}},
        "/with_ref": {"get": {"responses": {"200": {
            "description": "schema with refs",
            "content": {"application/json": {
                "schema": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/reffed"}

                }
            }}
        }}}},
        "/with_nullable": {"get": {"responses": {"200": {
            "description": "schema with nullable values",
            "content": {"application/json": {
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "nullable": True
                    }
                }
            }}
        }}}}
    },
    "components": {
        "schemas": {
            "reffed": {
                "type": "object",
                "required": ["bar"],
                "properties": {
                    "bar": {"$ref": "#/components/schemas/bar"},
                    "foo": {"type": "integer"},
                    "baz": {"$ref": "#/components/schemas/nullabar"}
                }
            },
            "bar": {
                "type": "string"
            },
            "nullabar": {
                "type": "integer",
                "nullable": True
            }
        }
    }
}


def test_openapi_spec_dict():
    spec = OpenApiSpec(TEST_SCHEMA)
    assert '/helloworld' in spec.get_paths()
    with pytest.raises(RuntimeError, match='Real path is not known'):
        p = spec.path
    assert spec.get_path_schema('/helloworld')['get']['responses']['200']['description'] == 'Computer says hello world'


def test_openapi_spec_from_version():
    spec = OpenApiSpec.from_version('0.4.0')
    assert '/' in spec.get_paths()
    assert isinstance(spec.path, pathlib.Path)
    assert spec.path.name == 'openeo-api-0.4.0.json'


def resp(body: Union[str, dict] = '', status: int = 200):
    """Factory for dummy responses"""
    r = Response()
    if isinstance(body, dict):
        body = json.dumps(body)
    r._content = body.encode('utf-8')
    r.status_code = status
    return r


@contextlib.contextmanager
def nullcontext():
    yield


class TestPurePythonValidator:

    def test_validator(self):
        validator = PurePythonValidator(spec=OpenApiSpec(TEST_SCHEMA))
        validator.validate_response(path='/helloworld', response=resp(body='{"greeting": "hello", "subject": "world"}'))
        validator.validate_response(path='/helloworld', response=resp(body='{"greeting": "hello"}'))
        with pytest.raises(jsonschema.ValidationError, match="'greeting' is a required property"):
            validator.validate_response(path='/helloworld', response=resp(body='{}'))

    def test_wrong_path(self):
        validator = PurePythonValidator(spec=OpenApiSpec(TEST_SCHEMA))
        with pytest.raises(ResponseNotInSchema):
            validator.validate_response(path='/foobar', response=resp(body='{"greeting": "hello"}'))

    @pytest.mark.parametrize(["valid", "body"], [
        (True, '[]'),
        (False, '[{}]'),
        (False, '[{"foo": 123}]'),
        (False, '[{"bar": 123}]'),
        (True, '[{"bar": "one"}]'),
        (True, '[{"bar": "one"}, {"bar": "two"}]'),
        (False, '[{"bar": "one"}, {"bar": 123}]'),
        (False, '[{"bar": "one", "foo": "two"}]'),
        (True, '[{"bar": "one", "foo": 123}]'),
    ])
    def test_ref_resolving(self, valid, body):
        validator = PurePythonValidator(spec=OpenApiSpec(TEST_SCHEMA))
        expectation = nullcontext() if valid else pytest.raises(jsonschema.ValidationError)
        with expectation:
            validator.validate_response(path='/with_ref', method='get', response=resp(body=body))

    @pytest.mark.parametrize(["valid", "body"], [
        (True, '[]'),
        (True, '["foo"]'),
        (True, '["foo", "bar"]'),
        (False, '["foo", 123]'),
        (False, '["foo", {"ba": "r"}]'),
        (True, '["foo", null]'),
    ])
    def test_nullable(self, valid, body):
        validator = PurePythonValidator(spec=OpenApiSpec(TEST_SCHEMA))
        expectation = nullcontext() if valid else pytest.raises(jsonschema.ValidationError)
        with expectation:
            validator.validate_response(path='/with_nullable', method='get', response=resp(body=body))

    @pytest.mark.parametrize(["valid", "body"], [
        (True, '[{"bar": "one"}]'),
        (False, '[{"bar": "one", "baz": "two"}]'),
        (True, '[{"bar": "one", "baz": 123}]'),
        (True, '[{"bar": "one", "baz": null}]'),
    ])
    def test_nullable_ref(self, valid, body):
        validator = PurePythonValidator(spec=OpenApiSpec(TEST_SCHEMA))
        expectation = nullcontext() if valid else pytest.raises(jsonschema.ValidationError)
        with expectation:
            validator.validate_response(path='/with_ref', method='get', response=resp(body=body))


def test_capabilities_has_endpoint():
    capabilities = Capabilities({
        'endpoints': [
            {'path': '/collections', 'methods': ['GET']},
        ]
    })
    assert capabilities.has_endpoint('/collections')
    assert capabilities.has_endpoint('/collections', method='get')
    assert capabilities.has_endpoint('/collections', method='GET')
    assert not capabilities.has_endpoint('/collections', method='POST')
    assert not capabilities.has_endpoint('/services', method='GET')
