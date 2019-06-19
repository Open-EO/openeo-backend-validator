# pytest based OpenEO API Validator

Python test suite to validate the API schema compliance of OpenEO backends.


# Set up

Create a virtual Python environment and install the dependencies:

    pip install -r requirements.txt


# Run

Run the test suite from the directory containing this README file.
You have to specify the API root url with `--backend` option.
When the API version can not be guessed from the backend url,
you also have to specify the expected API version
with option `--api-version`.
For example:

    pytest --backend http://openeo.vgt.vito.be/openeo/0.4.0
    pytest --backend https://earthengine.openeo.org/v0.3 --api-version 0.3.1

