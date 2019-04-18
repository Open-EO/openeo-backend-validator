# OpenEO compliance test using Go 

This standalone tool written in Go uses the Go package [kin-openapi](https://github.com/getkin/kin-openapi) to read the openapi definition and validates the response of the back end to self defined requests.

## Installation

### Install (Build it) using Go
1. Install Go on your computer by downloading it from the [download page](https://golang.org/dl/).
1. Clone this Github repository (e,g, git clone https://github.com/Open-EO/openeo-backend-validator.git). 
1. Change to the folder of the repository. 
1. Run the following command to build the executable out of openeoct.go. 
`go build openeoct.go
`
1. It then creates an executable in the same directory named "openeoct" ("openeoct.exe" on Windows)

Hint: If the build fails, you may have to install the dependencies manually by running the following commands:
```
go get github.com/getkin/kin-openapi/openapi3
go get github.com/getkin/kin-openapi/openapi3filter
go get github.com/urfave/cli
go get github.com/BurntSushi/toml
```

## Configuration
At the moment the tool needs a config file to forward the needed information (e.g. back end url, username etc.)
The config file follows the [TOML](https://github.com/toml-lang/toml) specification of config files and consists of the following elements:

*  *url* - the url of the back end that should be validated
*  *openapi* - the openEO openapi.json file that it will be validated against (ATM you should use the files in the repository, since I had to make minor modifications to make it run) 
*  *username* - username of the back end (empty or missing if there is no authentication needed)
*  *password* - password of the user (empty or missing if there is no authentication needed)
*  *authurl* - the authentication endpoint of the back end (e.g. "/credentials/basic" or empty/missing if there is no authentication needed)
*  *endpoints* - list of endpoints that should be tested at the back end (ATM only GET endpoints are supported).
*  *output* - output file, to store the validation results (missing if it should be written into stdout in the terminal)

There is an example config file[(gee_config.toml)](https://github.com/Open-EO/openeo-backend-validator/blob/master/openeoct/gee_config.toml) in this folder.

## Usage

To run the tool on the command line, you just have to set up the configuration file and provide it to the tool:

```
openeoct (or openeoct.exe) config PATH_TO_CONFIG_FILE
# e.g. on linux in this GitHub folder
./openeoct config gee_config.toml
```
The output is a JSON object that contains "VALID" for every endpoint that is valid against the openapi specification and an error message with further information for every endpoint that does not match the specification. 

Feel free to add an issue if you ran into problems, but please look first into the existing ones.
