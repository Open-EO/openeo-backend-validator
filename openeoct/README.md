# OpenEO compliance test using Go 

This standalone tool written in Go uses the Go package [kin-openapi](https://github.com/getkin/kin-openapi) to read the openapi definition and validates the response of the back end to self defined requests.
In the flask folder there is a simple web application GUI for this tool also available on a public instance [here](https://www.geo.tuwien.ac.at/openeoct).

## Building

1. Install Go on your computer, e.g. by downloading it from the [download page](https://golang.org/dl/).
1. Clone this Github repository (e.g. `git clone https://github.com/Open-EO/openeo-backend-validator.git`). 
1. Change to the `openeoct` folder of the repository. 
1. Run the following command to build the executable out of `openeoct.go`:

        go build openeoct.go

    If the build fails because of missing dependencies, install them first as follows:

        go get github.com/Open-EO/openeo-backend-validator/openeoct/kin-openapi/openapi3
        go get github.com/Open-EO/openeo-backend-validator/openeoct/kin-openapi/openapi3filter
        go get github.com/urfave/cli
        go get github.com/BurntSushi/toml

1. this creates an executable in the same directory named "openeoct" ("openeoct.exe" on Windows)


## Configuration

At the moment the tool requires a config file in [TOML](https://github.com/toml-lang/toml) format
to specify the necessary information (e.g. back end url, username, etc):

*  *url* - the url of the back end that should be validated
*  *openapi* - the openEO openapi.json file/url it will be validated against 
*  *username* - username of the back end (empty or missing if there is no authentication needed)
*  *password* - password of the user (empty or missing if there is no authentication needed)
*  *authurl* - the authentication endpoint of the back end (e.g. "/credentials/basic" or empty/missing if there is no authentication needed)
*  *endpoints* - list of endpoints that should be tested at the back end. Endpoints can have a group attribute, to structure the output by the groups and an optional attribute, so that the validation does not fail, but prints that it does not work but is also not mandatory.
*  *output* - output file, to store the validation results (missing if it should be written into stdout in the terminal)

The values of the toml config file (except for endpoints) can be set to environment variables. For example by writing "$MY_URL" for the environemnt variable MY_URL.

There are example config files in the [examples folder](https://github.com/Open-EO/openeo-backend-validator/blob/master/openeoct/examples).

## Usage

To run the tool on the command line, provide the configuration file using the `config` command.
Example usage with the example `gee_config.toml` config file:

    ./openeoct config gee_config.toml

(On Windows: use "`openoct.exe`" instead of "`openeoct`").

The output is a JSON object that contains "Valid" for every endpoint that is valid against the openapi specification and an error message with further information for every endpoint that does not match the specification. 

Feel free to add an issue if you ran into problems, but please look first into the existing ones.
