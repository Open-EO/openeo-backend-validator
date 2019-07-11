"""
Reusable test fixtures
"""

import pytest

from openeo_compliance_tests.helpers import ApiClient, get_api_version, OpenApiSpec, PurePythonValidator


@pytest.fixture
def client(request):
    """Pytest fixture for an API client for desired backend."""
    return ApiClient(request.config.getoption("--backend"))


@pytest.fixture
def api_version(request):
    return get_api_version(request.config)


@pytest.fixture
def spec(api_version: str):
    return OpenApiSpec.from_version(api_version)


@pytest.fixture
def validator(spec: OpenApiSpec):
    return PurePythonValidator(spec)
