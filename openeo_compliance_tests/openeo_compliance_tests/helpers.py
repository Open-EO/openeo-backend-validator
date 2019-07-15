import abc
import json
import re
from pathlib import Path
from typing import Union, KeysView
from urllib.parse import urlparse

import _pytest.config
import jsonschema
import openapi_schema_to_json_schema
import pkg_resources
from requests import Session, Response


class ApiClient:
    """Simple `requests` based API client."""
    _timeout = 1

    def __init__(self, backend: str):
        self.s = Session()
        assert backend is not None
        self.backend = backend.rstrip('/')

    @property
    def domain(self):
        parsed = urlparse(self.backend)
        return '{s}://{d}'.format(s=parsed.scheme, d=parsed.netloc)

    def request(self, method: str, path: str, expect_status_code=200, **kwargs):
        assert path.startswith('/')
        timeout = kwargs.pop('timeout', self._timeout)
        response = self.s.request(method=method, url=self.backend + path, timeout=timeout, **kwargs)
        if expect_status_code:
            # TODO: allow specifying a list of status codes?
            assert response.status_code == expect_status_code
        return response

    def get(self, path: str, expect_status_code=200, **kwargs) -> Response:
        return self.request(method='get', path=path, expect_status_code=expect_status_code, **kwargs)


def get_backend(config: _pytest.config.Config):
    """
    Get OpenEo backend root URL as specified through `--backend` command line option.
    Note: will return None when no backend is specified.
    """
    return config.getoption('--backend')


def get_api_version(config: _pytest.config.Config):
    """
    Get/Guess API version from command line options (`--api-version` or `--backend`).
    Note: will return None when no API version information.
    """
    version = config.getoption('--api-version')
    if version:
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise Exception('Invalid API version: {v!r}'.format(v=version))
    else:
        # Try to guess from backend url
        backend = get_backend(config)
        if backend:
            match = re.search(r'(\d+)[._-](\d+)[._-](\d+)', backend)
            if not match:
                raise Exception('Failed to guess API version from backend url {b}.'.format(b=backend))
            version = '.'.join(match.groups())
        else:
            return None
    return version


class ResponseNotInSchema(KeyError):
    pass


class OpenApiSpec:
    """Helper to inspect and query OpenAPI spec"""

    def __init__(self, spec: Union[Path, dict]):
        """Load OpenAPI spec from file path or given as a dict (handy for testing)"""
        if isinstance(spec, Path):
            self._path = spec
            with spec.open(encoding='utf-8') as f:
                self._spec = json.load(f)
        elif isinstance(spec, dict):
            self._path = None
            self._spec = spec
        else:
            raise ValueError("Don't know how to handle {s!r}".format(s=spec))

    @classmethod
    def from_version(cls, version: str = '0.4.0') -> 'OpenApiSpec':
        assert version is not None
        p = pkg_resources.resource_filename('openeo_compliance_tests', 'schemas/openeo-api-{v}.json'.format(v=version))
        return cls(Path(p))

    @property
    def spec(self) -> dict:
        return self._spec

    @property
    def path(self) -> Path:
        if self._path is None:
            raise RuntimeError('Real path is not known')
        return self._path

    def get_paths(self) -> KeysView:
        return self._spec['paths'].keys()

    def get_path_schema(self, path: str) -> dict:
        return self._spec['paths'][path]


class OpenApiValidator(abc.ABC):
    """
    Base class for OpenAPI validators.

    Subclasses have to implement `validate_response`, which raises an exception when something is wrong
    """

    def __init__(self, spec: OpenApiSpec):
        self.api_spec = spec

    @abc.abstractmethod
    def validate_response(self, path: str, response: Response, method: str = 'get'):
        pass


class PurePythonValidator(OpenApiValidator):
    """
    Pure Python implementation of OpenAPI validation.

    Implemented using combination of `jsonschema` and `openapi_schema_to_json_schema` modules
    due to current lack of a dedicated OpenApi validation module
    """

    class _OpenApiResolver(jsonschema.RefResolver):
        """Custom resolver for OpenApi style $ref references"""

        def resolve(self, ref):
            url, schema = super().resolve(ref)
            # Handle JSONschema/OpenAPI conversions in resolved schema
            return url, openapi_schema_to_json_schema.to_json_schema(schema)

    def validate_response(self, path: str, response: Response, method: str = 'get'):
        # Get schema for given path
        try:
            path_spec = self.api_spec.get_path_schema(path)
            status = str(response.status_code)
            schema = path_spec[method]['responses'][status]['content']['application/json']['schema']
        except KeyError as e:
            raise ResponseNotInSchema(*e.args) from None

        # OpenApi 3 is closest to JSON Schema Draft, combined with some
        # conversions handled by openapi_schema_to_json_schema (also in resolver).
        resolver = self._OpenApiResolver.from_schema(schema=self.api_spec.spec)
        validator = jsonschema.Draft4Validator(
            schema=openapi_schema_to_json_schema.to_json_schema(schema),
            resolver=resolver
        )
        return validator.validate(instance=response.json())


class GoToolValidator(OpenApiValidator):
    """
    Validator based on custom `openeoct` validation tool in Go
    """

    def validate_response(self, path: str, response: Response, method: str = 'get'):
        # TODO
        spec_file_path = str(self.api_spec.path)
        status_code = response.status_code
        headers = response.headers
        body = response.text


class Capabilities:
    """Helper to query the capabilities of a backend."""

    def __init__(self, capabilities: dict):
        self.capabilities = capabilities

    def has_endpoint(self, endpoint, method='get'):
        return any(
            e['path'] == endpoint and method.lower() in set(m.lower() for m in e['methods'])
            for e in self.capabilities['endpoints']
        )
