import json
import pkgutil
import re
from urllib.parse import urlparse

import _pytest.config
import jsonschema
from requests import Session, Response


class ApiClient:
    """Simple `requests` based API client."""
    _timeout = 1

    def __init__(self, backend: str):
        self.s = Session()
        self.backend = backend.rstrip('/')

    @property
    def domain(self):
        parsed = urlparse(self.backend)
        return '{s}://{d}'.format(s=parsed.scheme, d=parsed.netloc)

    def get(self, path: str) -> Response:
        assert path.startswith('/')
        return self.s.get(self.backend + path, timeout=self._timeout)

    def get_json(self, path: str) -> dict:
        r = self.get(path)
        r.raise_for_status()
        return r.json()


def get_api_version(config: _pytest.config.Config):
    """Get/Guess API version from pytest config"""
    version = config.getoption('--api-version')
    if version:
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise Exception('Invalid API version: {v!r}'.format(v=version))
    else:
        # Try to guess from backend url
        backend = config.getoption("--backend")
        match = re.search(r'(\d+)[._-](\d+)[._-](\d+)', backend)
        if not match:
            raise Exception('Failed to guess API version from backend url {b}.'.format(b=backend))
        version = '.'.join(match.groups())
    return version


class ResponseNotInSchema(KeyError):
    pass


class ApiSchemaValidator:
    """
    Helper class to load an OpenEo API schema definition
    and build a validator for desired subschema.
    """

    def __init__(self, schema: dict):
        assert 'paths' in schema
        self._schema = schema

    @classmethod
    def from_filename(cls, name='openeo-api-0.4.0.json') -> 'ApiSchemaValidator':
        """Load ApiSchema from schemas folder by filename"""
        schema_json = pkgutil.get_data('openeo_compliance_tests', 'schemas/{n}'.format(n=name)).decode('utf-8')
        return cls(json.loads(schema_json))

    @classmethod
    def from_version(cls, version='0.4.0') -> 'ApiSchemaValidator':
        """Load ApiSchema from schemas folder by API version."""
        return cls.from_filename('openeo-api-{v}.json'.format(v=version))

    def _get_validator(self, expected_schema: dict) -> jsonschema.Draft4Validator:
        resolver = jsonschema.RefResolver.from_schema(self._schema)
        # OpenApi 3 is closest to JSON Schema Draft 4
        validator = jsonschema.Draft4Validator(expected_schema, resolver=resolver)
        return validator

    def get_response_validator(self, path: str = '/', operation: str = 'get', code: str = '200',
                               media_type: str = 'application/json', ) -> jsonschema.Draft4Validator:
        """Helper to get the response schema of a given request path"""
        try:
            schema = self._schema['paths'][path][operation]['responses'][code]['content'][media_type]['schema']
        except KeyError as e:
            raise ResponseNotInSchema(*e.args) from None
        return self._get_validator(schema)

    def get_paths(self):
        return self._schema['paths'].keys()

    def get_path_schema(self, path: str):
        return self._schema['paths'][path]
