# pytest based OpenEO API Validator

Python test suite to validate the API schema compliance of OpenEO backends.


# Set up

Create a virtual Python environment and install the dependencies:

    pip install -r requirements.txt


# Running the test suite

Run the test suite from the directory containing this README file.
You have to specify the API root url with `--backend` option.

    pytest --backend http://openeo.vgt.vito.be/openeo/0.4.0

When the API version can not be guessed from the backend url
(`0.4.0` in the example above),
you also have to specify the expected API version with option `--api-version`.
For example:

    pytest --backend https://earthengine.openeo.org/v0.3 --api-version 0.3.1

## Options and output

Being a standard pytest powered test suite, you can use
normal pytest features and finetuning options.

For example: generate a **JUnit** XML report by adding the option `--junitxml=report.xml`).
You can also generate a **HTML** report by adding option `--html=report.html`.


Limit the coverage of the test suite run based on file or function name with the [`-k EXPRESSION` option](https://docs.pytest.org/en/latest/example/markers.html#using-k-expr-to-select-tests-based-on-their-name).
For example to run only the error handling tests, excepts the ones about "invalid_path", add:

    -k "error_handling.py and not invalid"


