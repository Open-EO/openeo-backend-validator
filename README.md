# OpenEO compliance tests

[![Build Status](https://travis-ci.org/Open-EO/openeo-backend-validator.svg?branch=master)](https://travis-ci.org/Open-EO/openeo-backend-validator)

There are two tools in this repository to tackle the issue of compliance testing:

1. *[openeo_compliance_tests](https://github.com/Open-EO/openeo-backend-validator/tree/master/openeo_compliance_tests)*
  Python testing framework to validate back end endpoints (only GET), by reading from an JSON OpenAPI specification file.
1. *[openeoct](https://github.com/Open-EO/openeo-backend-validator/tree/master/openeoct)*
  Go standalone tool that validates single back end endpoints defined in a config file, by using an validation package of Go.

Further information about the tools are in their folders.
