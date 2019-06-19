"""
Reusable test fixtures
"""
import re

import pytest

from openeo_compliance_tests.helpers import ApiClient, ApiSchemaValidator


@pytest.fixture
def client(request):
    """Pytest fixture for an API client for desired backend."""
    return ApiClient(request.config.getoption("--backend"))


@pytest.fixture
def api_version(request):
    version = request.config.getoption('--api-version')
    if version:
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise Exception('Invalid API version: {v!r}'.format(v=version))
    else:
        # Try to guess from backend url
        backend = request.config.getoption("--backend")
        match = re.search(r'(\d+)[._-](\d+)[._-](\d+)', backend)
        if not match:
            raise Exception('Failed to guess API version from backend url {b}.'.format(b=backend))
        version = '.'.join(match.groups())
    return version


@pytest.fixture
def schema(api_version) -> ApiSchemaValidator:
    """Pytest fixture for expected API schema for desired version"""
    return ApiSchemaValidator.from_version(api_version)
