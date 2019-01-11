import pytest
import requests
from openeo_compliance_tests.client import Client

def pytest_addoption(parser):
    parser.addoption(
        "--backend", action="store", default="http://openeo.vgt.vito.be/openeo/0.4.0/", help="Provide backend url"
    )


@pytest.fixture
def backend(request):
    """
    Client to use when doing backend requests.
    """
    return Client(request.config.getoption("--backend"))