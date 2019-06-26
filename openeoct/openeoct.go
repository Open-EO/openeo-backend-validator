package main

import (
	"context"
	"encoding/json"
	"io/ioutil"
	"log"
	"net/http"
	"os"

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
	id           int
	url          string
	request_type string
	body         string
	header       string
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
			states[endpoint.url] = err.msg
		} else {
			states[endpoint.url] = state
		}
	}
	return states
}

// Validates a single endpoint defined as input parameter.
// Returns the resulting state and an error message if something went wrong.
func (ct *ComplianceTest) validate(endpoint Endpoint) (string, *ErrorMessage) {
	//log.Println(openapi3.SchemaStringFormats)
	//openapi3.DefineStringFormat("url", `^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)
	//log.Println(openapi3.SchemaStringFormats)

	swagger, err := openapi3.NewSwaggerLoader().LoadSwaggerFromFile(ct.apifile)

	// if err := swagger.Validate(context.TODO()); err != nil {
	// 	log.Println(err)
	// }

	router := openapi3filter.NewRouter().WithSwagger(swagger)
	ctx := context.TODO()

	token := ""

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

	method := http.MethodGet

	if endpoint.request_type == "POST" {
		method = http.MethodPost
	}

	httpReq, _ := http.NewRequest(method, endpoint.url, nil)

	if token != "" {
		bearer := "Bearer " + token
		httpReq.Header.Add("Authorization", bearer)
	}

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error parsing the OpenEO API file: \n" + err.Error()
		return "Error1", errormsg
	}
	// Find route
	route, pathParams, err := router.FindRoute(httpReq.Method, httpReq.URL)

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error finding endpoint in the OpenAPI definition: \n" + err.Error()
		return "Error2", errormsg
	}

	// Options
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
		Options:    options,
	}

	if err := openapi3filter.ValidateRequest(ctx, requestValidationInput); err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error validating the request: \n" + err.Error()
		return "Error3", errormsg
	}

	client := &http.Client{}

	execReq, _ := http.NewRequest(http.MethodGet, ct.backend.url+endpoint.url, nil)
	if token != "" {
		bearer := "Bearer " + token
		execReq.Header.Add("Authorization", bearer)
	}
	resp, err := client.Do(execReq)

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.msg = "Error sending request to back end: \n" + err.Error()
		return "Error4", errormsg
	}
	body, err := ioutil.ReadAll(resp.Body)

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
	Endpoints []string
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

// 	config = ReadConfig("gee_config_v4.toml")

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

// 	var ep_array []Endpoint
// 	for _, endpoint := range config.Endpoints {

// 		ep := Endpoint{url: endpoint, request_type: "GET"}

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
	app.Commands = []cli.Command{
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

	// define back end and compliance test instance
	ct := new(ComplianceTest)
	ct.backend.url = config.Url
	ct.apifile = config.Openapi

	ct.username = config.Username
	ct.password = config.Password
	ct.authendpoint = config.Authurl

	var ep_array []Endpoint
	for _, endpoint := range config.Endpoints {

		ep := Endpoint{url: endpoint, request_type: "GET"}

		ep_array = append(ep_array, ep)
	}

	ct.endpoints = ep_array

	// state, err := ct.validate(config.Endpoints)
	//log.Println("Result: ", state)
	//if err != nil {
	//		log.Println("Error: ", err.msg)
	//	}

	//	ct.endpoints = []string{"/", "/collections", "/service_types"}

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
