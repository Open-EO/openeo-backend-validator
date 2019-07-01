"""
pytest configuration file
"""

import _pytest.config

from openeo_compliance_tests.helpers import get_backend, get_api_version


def pytest_addoption(parser):
    parser.addoption(
        "--backend", action="store", default=None, help="Backend url to validate."
    )
    parser.addoption(
        "--api-version", action="store", default=None, help="API version to expect."
    )


def pytest_configure(config: _pytest.config.Config):
    # Add backend and API version to "environment" section of HTML report.
    config._metadata['OpenEO backend'] = get_backend(config)
    config._metadata['OpenEO API version'] = get_api_version(config)
