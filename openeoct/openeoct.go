package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/Open-EO/openeo-backend-validator/openeoct/kin-openapi/openapi3"
	"github.com/Open-EO/openeo-backend-validator/openeoct/kin-openapi/openapi3filter"

	"github.com/BurntSushi/toml"
	"github.com/urfave/cli"
)

// ErrorMessage "class"
type ErrorMessage struct {
	msg string
}

// Back end "class"
type BackEnd struct {
	url string
	// Add auth and that stuff
}

// Endpoint "class"
type Endpoint struct {
	Id           string
	Url          string
	Request_type string
	Body         string
	Header       string
	// Add auth and that stuff
}

// ComplianceTest "class"
type ComplianceTest struct {
	backend      BackEnd
	apifile      string
	endpoints    []Endpoint
	authendpoint string
	username     string
	password     string
}

// Validates all enpoints defined in the compliance test instance.
// Returns a map of strings containing the states of the validation results
func (ct *ComplianceTest) validateAll() map[string]string {

	states := make(map[string]string)

	for _, endpoint := range ct.endpoints {
		state, err := ct.validate(endpoint)
		if err != nil {
			states[endpoint.Url] = err.msg
		} else {
			states[endpoint.Url] = state
		}
	}
	return states
}

func (ct *ComplianceTest) buildRequest(endpoint Endpoint, token string, abs_url bool) (*http.Request, string) {

	method := http.MethodGet

	if endpoint.Request_type == "POST" {
		method = http.MethodPost
	} else if endpoint.Request_type == "PATCH" {
		method = http.MethodPatch
	} else if endpoint.Request_type == "PUT" {
		method = http.MethodPut
	} else if endpoint.Request_type == "DELETE" {
		method = http.MethodDelete
	}

	httpReq, _ := http.NewRequest(method, endpoint.Url, nil)

	if abs_url == true {
		httpReq, _ = http.NewRequest(method, ct.backend.url+endpoint.Url, nil)
	}

	if token != "" {
		bearer := "Bearer " + token
		httpReq.Header.Add("Authorization", bearer)
	}

	if _, err := os.Stat(endpoint.Body); err == nil {
		httpReq.Header.Set("Content-Type", "application/json")

		dat, err := ioutil.ReadFile(endpoint.Body)
		if err != nil {
			// errormsg := new(ErrorMessage)
			// errormsg.msg = "Error loading body file: " + err.Error()
			// return "Error0", errormsg
			return httpReq, ""
		}

		stringReader := strings.NewReader(string(dat))
		stringReadCloser := ioutil.NopCloser(stringReader)
		httpReq.Body = stringReadCloser

	} else if os.IsNotExist(err) {
		// path/to/whatever does *not* exist
		if !(endpoint.Body == "") {
			log.Println(endpoint.Url, ": Body was set in config file, but the file does not exist: ", endpoint.Body)
			return httpReq, fmt.Sprintf("%s: Body was set in config file, but the file does not exist: %s", endpoint.Url, endpoint.Body)
		}
	}

	return httpReq, ""

}

// Validates a single endpoint defined as input parameter.
// Returns the resulting state and an error message if something went wrong.
func (ct *ComplianceTest) validate(endpoint Endpoint) (string, *ErrorMessage) {
	//log.Println(openapi3.SchemaStringFormats)
	//openapi3.DefineStringFormat("url", `^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)
	//log.Println(openapi3.SchemaStringFormats)

	_, err := os.Stat(ct.apifile)

	// Try to read the openapi3 file
	swagger, err := openapi3.NewSwaggerLoader().LoadSwaggerFromFile(ct.apifile)

	if err != nil {
		// openapi3 file not found, assume it is an URI
		apiReq, _ := http.NewRequest(http.MethodGet, ct.apifile, nil)
		swagger, err = openapi3.NewSwaggerLoader().LoadSwaggerFromURI(apiReq.URL)
	}

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error reading the openEO API, neighter file nor url found : \n" + err.Error()
		return "Error1", errormsg
	}

	router := openapi3filter.NewRouter().WithSwagger(swagger)
	ctx := context.TODO()

	token := ""

	// Set Authentication Token
	if ct.username != "" && ct.password != "" && ct.authendpoint != "" {

		client := &http.Client{}

		httpReq, _ := http.NewRequest(http.MethodGet, ct.backend.url+ct.authendpoint, nil)
		httpReq.SetBasicAuth(ct.username, ct.password)
		resp, _ := client.Do(httpReq)
		if resp.StatusCode == 200 {
			body, _ := ioutil.ReadAll(resp.Body)
			m := make(map[string]interface{})
			json.Unmarshal(body, &m)
			token, _ = m["access_token"].(string)

		}
	}

	// Define Request
	httpReq, errReq := ct.buildRequest(endpoint, token, false)

	if errReq != "" {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error processing the Config file: \n" + errReq
		return "Error1", errormsg
	}

	// Find route in openAPI definition
	route, pathParams, err := router.FindRoute(httpReq.Method, httpReq.URL)

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error finding endpoint in the OpenAPI definition: \n" + err.Error()
		return "Error2", errormsg
	}

	// Options for the validation
	options := &openapi3filter.Options{
		AuthenticationFunc: func(c context.Context, input *openapi3filter.AuthenticationInput) error {
			// TODO: support more schemes
			sec := input.SecurityScheme
			if sec.Type == "http" && sec.Scheme == "bearer" {
				if httpReq.Header.Get("Authorization") == "" {
					return nil //errors.New("Missing auth")
				}
			}
			return nil
		},
	}

	// Validate request
	requestValidationInput := &openapi3filter.RequestValidationInput{
		Request:    httpReq,
		PathParams: pathParams,
		Route:      route,
		Options:    options}

	if err := openapi3filter.ValidateRequest(ctx, requestValidationInput); err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error validating the request: \n" + err.Error()
		return "Error3", errormsg
	}

	// Send request
	client := &http.Client{}

	execReq, errReq := ct.buildRequest(endpoint, token, true)

	resp, err := client.Do(execReq)

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error sending request to back end: \n" + err.Error()
		return "Error4", errormsg
	}

	// Get Response
	body, err := ioutil.ReadAll(resp.Body)

	// log.Println(string(body))

	if resp.StatusCode == 401 {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error: Authentication failed, currently only BasicAuth is supported."
		return "Error", errormsg
	}

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error reading response from the back end: \n" + err.Error()
		return "Error5", errormsg
	}

	var (
		respStatus = resp.StatusCode
		respHeader = resp.Header
		respBody   = string(body)
	)

	// Define validation input
	responseValidationInput := &openapi3filter.ResponseValidationInput{
		RequestValidationInput: requestValidationInput,
		Status:                 respStatus,
		Header:                 respHeader}

	if respBody != "" {
		responseValidationInput.SetBodyBytes([]byte(respBody))
	}

	// Validate response.
	if err := openapi3filter.ValidateResponse(ctx, responseValidationInput); err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Response of the back end not valid: \n" + err.Error()
		return "Not Valid", errormsg
	}

	return "Valid", nil
}

// log.Println(ExternValidateResponse("https://raw.githubusercontent.com/Open-EO/openeo-api/0.4.1/openapi.json", "/", "GET", 200, "", ""))
func ExternValidateResponse(openapi_path string, endpoint_path string, endpoint_type string, response_status int, response_body string, response_header string) string {
	ct := new(ComplianceTest)
	//ct.backend.url = config.Url
	ct.apifile = openapi_path

	endpoint := new(Endpoint)
	endpoint.Id = "Test"
	endpoint.Url = endpoint_path
	endpoint.Request_type = endpoint_type

	resp := new(http.Response)

	resp.StatusCode = response_status
	resp.Body = ioutil.NopCloser(strings.NewReader(response_body))
	//resp.Header = response_header

	state, err := ct.validateResponse(*endpoint, resp)

	if err != nil {
		return err.msg
	} else {
		return state
	}

}

// Validates a single endpoint against a given response from the backend.
// Returns the resulting state and an error message if something went wrong.
func (ct *ComplianceTest) validateResponse(endpoint Endpoint, response *http.Response) (string, *ErrorMessage) {
	//log.Println(openapi3.SchemaStringFormats)
	//openapi3.DefineStringFormat("url", `^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)
	//log.Println(openapi3.SchemaStringFormats)

	_, err := os.Stat(ct.apifile)

	// Try to read the openapi3 file
	swagger, err := openapi3.NewSwaggerLoader().LoadSwaggerFromFile(ct.apifile)

	if err != nil {
		// openapi3 file not found, assume it is an URI
		apiReq, _ := http.NewRequest(http.MethodGet, ct.apifile, nil)
		swagger, err = openapi3.NewSwaggerLoader().LoadSwaggerFromURI(apiReq.URL)
	}

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error reading the openEO API, neighter file nor url found : \n" + err.Error()
		return "Error1", errormsg
	}

	router := openapi3filter.NewRouter().WithSwagger(swagger)
	ctx := context.TODO()

	token := ""

	// Set Authentication Token
	if ct.username != "" && ct.password != "" && ct.authendpoint != "" {

		client := &http.Client{}

		httpReq, _ := http.NewRequest(http.MethodGet, ct.backend.url+ct.authendpoint, nil)
		httpReq.SetBasicAuth(ct.username, ct.password)
		resp, _ := client.Do(httpReq)
		if resp.StatusCode == 200 {
			body, _ := ioutil.ReadAll(resp.Body)
			m := make(map[string]interface{})
			json.Unmarshal(body, &m)
			token, _ = m["access_token"].(string)

		}
	}

	// Define Request
	httpReq, errReq := ct.buildRequest(endpoint, token, false)

	if errReq != "" {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error processing the Config file: \n" + errReq
		return "Error1", errormsg
	}

	// Find route in openAPI definition
	route, pathParams, err := router.FindRoute(httpReq.Method, httpReq.URL)

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error finding endpoint in the OpenAPI definition: \n" + err.Error()
		return "Error2", errormsg
	}

	// Options for the validation
	options := &openapi3filter.Options{
		AuthenticationFunc: func(c context.Context, input *openapi3filter.AuthenticationInput) error {
			// TODO: support more schemes
			sec := input.SecurityScheme
			if sec.Type == "http" && sec.Scheme == "bearer" {
				if httpReq.Header.Get("Authorization") == "" {
					return nil //errors.New("Missing auth")
				}
			}
			return nil
		},
	}

	// Validate request
	requestValidationInput := &openapi3filter.RequestValidationInput{
		Request:    httpReq,
		PathParams: pathParams,
		Route:      route,
		Options:    options}

	if err := openapi3filter.ValidateRequest(ctx, requestValidationInput); err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error validating the request: \n" + err.Error()
		return "Error3", errormsg
	}

	// Send request
	//client := &http.Client{}

	//execReq, errReq := ct.buildRequest(endpoint, token, true)

	// resp, err := client.Do(execReq)

	// if err != nil {
	// 	errormsg := new(ErrorMessage)
	// 	errormsg.msg = "Error sending request to back end: \n" + err.Error()
	// 	return "Error4", errormsg
	// }

	// Get Response
	body, err := ioutil.ReadAll(response.Body)

	// log.Println(string(body))

	if response.StatusCode == 401 {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error: Authentication failed, currently only BasicAuth is supported."
		return "Error", errormsg
	}

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error reading response from the back end: \n" + err.Error()
		return "Error5", errormsg
	}

	var (
		respStatus = response.StatusCode
		respHeader = response.Header
		respBody   = string(body)
	)

	// Define validation input
	responseValidationInput := &openapi3filter.ResponseValidationInput{
		RequestValidationInput: requestValidationInput,
		Status:                 respStatus,
		Header:                 respHeader}

	if respBody != "" {
		responseValidationInput.SetBodyBytes([]byte(respBody))
	}

	// Validate response.
	if err := openapi3filter.ValidateResponse(ctx, responseValidationInput); err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Response of the back end not valid: \n" + err.Error()
		return "Not Valid", errormsg
	}

	return "Valid", nil
}

// Elements of the Config file

type Config struct {
	Url       string
	Openapi   string
	Username  string
	Password  string
	Authurl   string
	Endpoints map[string]Endpoint
	Output    string
}

// Reads info from config file
func ReadConfig(config_file string) Config {
	var configfile = config_file
	_, err := os.Stat(configfile)
	if err != nil {
		log.Fatal("Config file is missing: ", configfile)
	}

	var config Config
	if _, err := toml.DecodeFile(configfile, &config); err != nil {
		log.Fatal(err)
	}
	//log.Print(config.Index)
	return config
}

// Testing Main function

// func main() {

// 	// Config file path
// 	var config Config

// 	// CLI handling
// 	// app := cli.NewApp()
// 	// app.Name = "openeoct"
// 	// app.Name = "openeoct"
// 	// app.Version = "0.1.0"
// 	// app.Usage = "validating a back end against an openapi description file!"

// 	// // add config command
// 	// app.Commands = []cli.Command{
// 	// 	{
// 	// 		Name:    "config",
// 	// 		Aliases: []string{"c"},
// 	// 		Usage:   "load from config file",
// 	// 		Action: func(c *cli.Context) error {
// 	// 			//configfile = c.Args().First()
// 	// 			config = ReadConfig(c.Args().First())
// 	// 			//log.Println("Configfile1: ", config.Url)
// 	// 			return nil
// 	// 		},
// 	// 	},
// 	// }

// 	// // run CLI
// 	// apperr := app.Run(os.Args)
// 	// if apperr != nil {
// 	// 	log.Fatal(apperr)
// 	// }

// 	config = ReadConfig("examples/gee_config_v4_external.toml")

// 	// config file read correctly
// 	if config.Url == "" {
// 		log.Println("Error: No config file specified")
// 	}

// 	// define back end and compliance test instance
// 	ct := new(ComplianceTest)
// 	ct.backend.url = config.Url
// 	ct.apifile = config.Openapi

// 	ct.username = config.Username
// 	ct.password = config.Password
// 	ct.authendpoint = config.Authurl

// 	//	log.Println(config.Endpoints)

// 	var ep_array []Endpoint
// 	for name, ep := range config.Endpoints {
// 		if ep.Id == "" {
// 			ep.Id = name
// 		}
// 		ep_array = append(ep_array, ep)
// 	}

// 	ct.endpoints = ep_array

// 	// state, err := ct.validate(config.Endpoints)
// 	//log.Println("Result: ", state)
// 	//if err != nil {
// 	//		log.Println("Error: ", err.msg)
// 	//	}

// 	//	ct.endpoints = []string{"/", "/collections", "/service_types"}

// 	// Run validation
// 	ct.listEndpoints()

// 	result := ct.validateAll()

// 	jsonString, _ := json.Marshal(result)

// 	// Write to log stdout or to output file
// 	if config.Output == "" {
// 		log.Println("Result:", string(jsonString))
// 	} else {
// 		ioutil.WriteFile(config.Output, jsonString, 0644)
// 	}

// }

// Main function
func main() {

	// Config file path
	var config Config

	// CLI handling
	app := cli.NewApp()
	app.Name = "openeoct"
	app.Name = "openeoct"
	app.Version = "0.1.0"
	app.Usage = "validating a back end against an openapi description file!"

	// add config command
	app.Commands = []*cli.Command{
		{
			Name:    "config",
			Aliases: []string{"c"},
			Usage:   "load from config file",
			Action: func(c *cli.Context) error {
				//configfile = c.Args().First()
				config = ReadConfig(c.Args().First())
				//log.Println("Configfile1: ", config.Url)
				return nil
			},
		},
	}

	// run CLI
	apperr := app.Run(os.Args)
	if apperr != nil {
		log.Fatal(apperr)
	}

	// config file read correctly
	if config.Url == "" {
		log.Println("Error: No config file specified")
	}

	// config = ReadConfig("examples/gee_config_v1_0_0_external.toml")
	// define back end and compliance test instance
	ct := new(ComplianceTest)
	ct.backend.url = config.Url
	ct.apifile = config.Openapi

	ct.username = config.Username
	ct.password = config.Password
	ct.authendpoint = config.Authurl

	var ep_array []Endpoint
	for name, ep := range config.Endpoints {
		if ep.Id == "" {
			ep.Id = name
		}
		ep_array = append(ep_array, ep)
	}

	ct.endpoints = ep_array

	// Run validation
	result := ct.validateAll()

	jsonString, _ := json.Marshal(result)

	// Write to log stdout or to output file
	if config.Output == "" {
		log.Println("Result:", string(jsonString))
	} else {
		ioutil.WriteFile(config.Output, jsonString, 0644)
	}

}
