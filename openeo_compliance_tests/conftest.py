"""
pytest configuration file
"""


def pytest_addoption(parser):
    parser.addoption(
        "--backend", action="store", default=None, help="Backend url to validate."
    )
    parser.addoption(
        "--api-version", action="store", default=None, help="API version to expect."
    )
