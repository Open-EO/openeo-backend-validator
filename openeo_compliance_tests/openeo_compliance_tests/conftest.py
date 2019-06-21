"""
Reusable test fixtures
"""

import pytest

from openeo_compliance_tests.helpers import ApiClient, ApiSchemaValidator, get_api_version


@pytest.fixture
def client(request):
    """Pytest fixture for an API client for desired backend."""
    return ApiClient(request.config.getoption("--backend"))


@pytest.fixture
def api_version(request):
    return get_api_version(request.config)


@pytest.fixture
def schema(api_version) -> ApiSchemaValidator:
    """Pytest fixture for expected API schema for desired version"""
    return ApiSchemaValidator.from_version(api_version)
