## Python Backend Validator

Python test suite to validate the compliance of OpenEO backends.

## Running the tests
Make sure all dependencies are available:

`pip install --user -r requirements.txt
`

Run the tests, from the top-level directory:
```
pytest --backend https://earthengine.openeo.org/v0.3
pytest --backend http://openeo.vgt.vito.be/openeo/0.4.0
```
