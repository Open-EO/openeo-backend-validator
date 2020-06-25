# OpenEO compliance test using Go 

This standalone tool written in Go uses the Go package [kin-openapi](https://github.com/getkin/kin-openapi) to read the openapi definition and validates the response of the back end to self defined requests.
In the flask folder there is a simple web application GUI for this tool also available on a public instance [here](https://www.geo.tuwien.ac.at/openeoct).

## Building

1. Install Go on your computer, e.g. by downloading it from the [download page](https://golang.org/dl/).
1. Clone this Github repository (e.g. `git clone https://github.com/Open-EO/openeo-backend-validator.git`). 
1. Change to the `openeoct` folder of the repository. 
1. First, install the dependencies by calling the following commands:
```
        go get github.com/Open-EO/openeo-backend-validator/openeoct/kin-openapi/openapi3
        go get github.com/Open-EO/openeo-backend-validator/openeoct/kin-openapi/openapi3filter
        go get github.com/urfave/cli
        go get github.com/BurntSushi/toml
        go get github.com/mcuadros/go-version
```
1. Run the following command to build the executable out of `openeoct.go`:

        go build openeoct.go

1. this creates an executable in the same directory named "openeoct" ("openeoct.exe" on Windows)


## Configuration

At the moment the tool requires at least one config file in [TOML](https://github.com/toml-lang/toml) or JSON format. In this guide we will focus on the TOML format. The following properties are configurable: 

*  *url (required)* - the base url of the backend that should be validated, if versioning is implemented by the backend (via [/.well-known/openeo](https://openeo.org/documentation/1.0/developers/api/reference.html#operation/connect)) , this has to be the url without the version. So for example `https://earthengine.openeo.org` instead of `https://earthengine.openeo.org/v1.0`.
`url="https://earthengine.openeo.org"`
*  *openapi (required)* - the openEO openapi(.yaml/.json) file/url it will be validated against 
`openapi="https://gist.githubusercontent.com/bgoesswe/8459bd57202e05a2951c130a2168ce3a/raw/8a43112d027df58f1e8fd3c069d975cee5087fd8/openeoapi-1.0.0rc2.json"`
*  *endpoints (required)* - list of endpoints that should be tested at the back end. Endpoints can have a group attribute, to structure the output by the groups and an optional attribute, so that the validation does not fail, but prints that it is invalid and not mandatory.
```
[endpoints]
  [endpoints.capabilities]
  url = "/"
  request_type="GET"
```
* *backendversion* - if the backend supports versioning, you can specify here the version you want to validate. Note that it has to be the exact version of the backend specified at the well-known endpoint of the backend (see "api_version" attribute). If the version does not exist, it will print a warning into the console and uses the base url fom the "url" property.
`backendversion = "1.0.0-rc.2"`
*  *username* - username of your user at the back end (empty or missing if there is no authentication needed)
`username="myuser"`
*  *password* - password of the user (empty or missing if there is no authentication needed)
`password="myuser12345"`
*  *output* - output file, to store the JSON validation results (missing if it should be written into stdout of the terminal)
`output="val_out.json"`
*  *variables* - list of variables definitions, which can be used in the endpoints.
```
[variables]
  myvar = "myvarvalue"
```
*  *config* - additional config file. The validator will merge the configurations, see section below for details.
`config="additional_config.toml"`
*  *authurl (deprecated)* - the authentication endpoint of the back end (defaults to "/credentials/basic")

`authurl="/credentials/basic"`

There are example config files in the [examples folder](https://github.com/Open-EO/openeo-backend-validator/blob/master/openeoct/examples).

### Environment Variables

The values of the toml config file (except for endpoints) can be set to environment variables. For example by writing "$MY_URL" for the environment variable MY_URL.
The following example will read the value of the password from the environment variable named "my_pwd".
```
password="$my_pwd"
```
Note that this has only been tested in a Linux environment, but should theoretically also work on Windows.

### Endpoints Definition

In the config file all endpoints need to be defined after the [endpoints] section. Each endpoint can have the following properties:
* *id (required)* - Unique (within the config file) identifier for the endpoint. It is used to reference the endpoint on an error messages or in the validation output.

`[endpoints.ENDPOINT_ID]` or `id="ENDPOINT_ID"`
* *url (required)* - Endpoint url, which will be appended to the backend url to build the complete url for validation.

`url = "/processes"`
* *request_type (required)* - [HTTP type/method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) of the request.

`request_type = "GET"`
* *body* - file path to a JSON file containing the body that should be sent with the endpoint during validation.

`body = "examples/body/processgraph_endpoint_gee.json"`
* *group* - the output is structured via endpoint groups, all endpoints with the same group name are in one group (defaults to "nogroup").
`group = "Process Endpoints"`
* *optional* - true if the endpoint is optional, meaning that the group validation summary is valid even if it failed (defaults to false).

`optional = true`
* *timeout* - Integer of seconds the timeout for this endpoint should be set. Usually not needed, but if the endpoint takes some time it could cause problems.

`timeout = 20` 

* *order* - Integer to specify the order the endpoint validation should be done. The higher the number the later it will be validated, whereas several endpoints can have the same number. Defaults to 0, which is a special case and will be validated after all ordered endpoints. The order applies within each group (with no group being treated as a seperate group), but not over all specified endpoints.

`order = 1` 

The complete endpoints section in the config file looks similar to:
```
[endpoints]
  [endpoints.ENDPOINT_ID]
  url = "/processes"
  request_type = "GET"
  body = "examples/body/processgraph_endpoint_gee.json"
  group = "Process Endpoints"
  optional = true
  timeout = 20

  [endpoints.ENDPOINT_ID2]
  ...
```

### (Endpoint) Variables

You can define endpoint variables in the config file to be used in the endpoints sections via the variables section via a "{variable_name}" tag:

```
[variables]
myurl="test-id"

[endpoints]
  [endpoints.myendpoint1]
  url = "/jobs/{myurl}"
  request_type = "GET"

  [endpoints.myendpoint2]
  url = "/jobs/test-id"
  request_type = "GET"
```

In the example above endpoint1 and endpoint2 are equal. The variables can be used for every property of the endpoints except for the identifier.
This enables the user to define details of the endpoint via a different config file with the given variables (e.g. a body variable defining the concrete JSON.).

### Multiple Config Files Behaviour

Either if you pass more than one config file on the CLI arguments or set the "config" property in the config file, the behaviour of defining multiple config files is the same. When two config files are given, the endpoints and the variables are merged together, so both endpoints and variables are used for the validation. If the same variable (e.g. same variable name) or the same endpoint (e.g. same endpoint identifier) are in more than one file, the value of the last config file is set. All other config fields are set to the last added config file.
For example:
Configfile A:
```
url="https://earthengine.openeo.org"
backendversion = "1.0.0-rc.2"
openapi="openapi_1_0_0rc2.yaml"
username="usernameA"
password="test123"
[variables]
  test2 = "POST"
  test3 = "something"
[endpoints]
  [endpoints.processes]
  url = "/endpointA"
  request_type = "GET"
```
Configfile B:
```
username="usernameB"
[variables]
  test2 = "GET"
[endpoints]
  [endpoints.capabilities]
  url = "/"
  request_type = "GET"

  [endpoints.processes]
  url = "/endpointB"
  request_type = "{test2}"
```

Calling now the tool like `./openeoct config configfileA.toml configfileB.toml` results in the same as only having one config file like the following:
```
url="https://earthengine.openeo.org"
backendversion = "1.0.0-rc.2"
openapi="openapi_1_0_0rc2.yaml"
username="usernameB"
password="test123"
[variables]
  test2 = "GET"
  test3 = "something"
[endpoints]
  [endpoints.capabilities]
  url = "/"
  request_type = "GET"

  [endpoints.processes]
  url = "/endpointB"
  request_type = "{test2}"
```

## Execution

To run the tool on the command line, provide the configuration file using the `config` command.
Example usage with the example `gee_config.toml` config file:

    ./openeoct config gee_config1.toml gee_config2.toml gee_config3.json ...

(On Windows: use "`openeoct.exe`" instead of "`openeoct`").

Feel free to add an issue if you ran into problems, but please look first into the existing ones.


### JSON Output

The output is a JSON object containing the state "Valid" for every endpoint that is valid against the openapi specification, 
"Invalid" for every endpoint that is invalid with an error message with further information or with the state "Error" 
if something went wrong during the validation process (e.g. host not reachable).

Example output:
```json
{
    "Process Group": {
        "endpoints": {
            "job_write": {
                "message": "",
                "state": "Valid",
                "type": "GET",
                "url": "/processes"
            }
        },
        "group_summary": "Valid"
    },
    "nogroup": {
        "endpoints": {
            "GET": {
                "message": "Input: GET  /processes/{unknown_var}; Error: Error finding endpoint in the OpenAPI definition; Details: Path was not found",
                "state": "Invalid",
                "type": "GET",
                "url": "/processes/{unknown_var}"
            },
            "endpoint2": {
                "message": "",
                "state": "Valid",
                "type": "GET",
                "url": "/"
            },
            "endpoint3c": {
                "message": "",
                "state": "Valid",
                "type": "GET",
                "url": "/collections/FIRMS"
            },
        },
        "group_summary": "Invalid"
    }
}
```
