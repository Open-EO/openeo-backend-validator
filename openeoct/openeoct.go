package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"regexp"
	"strconv"
	"strings"

	"github.com/Open-EO/openeo-backend-validator/openeoct/kin-openapi/openapi3"
	"github.com/Open-EO/openeo-backend-validator/openeoct/kin-openapi/openapi3filter"

	"github.com/BurntSushi/toml"
	"github.com/urfave/cli"
)

// ErrorMessage "class"
type ErrorMessage struct {
	input  string
	output string
	msg    string
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
	Optional     bool
	Group        string
	// Add auth and that stuff
}

// ComplianceTest "class"
type ComplianceTest struct {
	backend      BackEnd
	apifile      string
	endpoints    map[string][]Endpoint
	authendpoint string
	username     string
	password     string
}

// Validates all enpoints defined in the compliance test instance.
// Returns a map of strings containing the states of the validation results
func (ct *ComplianceTest) validateAll() map[string](map[string]string) {

	states := make(map[string](map[string]string))

	for _, endpoints := range ct.endpoints {
		for _, endpoint := range endpoints {
			state, err := ct.validate(endpoint)
			states[endpoint.Id] = make(map[string]string)
			states[endpoint.Id]["state"] = state

			if err != nil {
				if endpoint.Optional == false {
					return_err := make(map[string]string)
					err_msg := err.output
					err_msg = strings.Replace(err_msg, "\n", "", -1)
					err_msg = strings.Replace(err_msg, "\"", "'", -1)
					space := regexp.MustCompile(`\s+`)
					err_msg = space.ReplaceAllString(err_msg, " ")
					err.output = err_msg
					return_err["input"] = err.input
					return_err["error"] = err.msg
					return_err["details"] = err.output
					states[endpoint.Id]["message"] = "Input: " + err.input + "; Error: " + err.msg + "; Details: " + err.output
				} else {
					states[endpoint.Id]["message"] = "Non-mandatory endpoint, not supported by back-end"
					states[endpoint.Id]["state"] = "Valid"
				}
			} else {
				states[endpoint.Id]["message"] = ""
			}
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
		bearer := "Bearer basic//" + token
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
		errormsg.input = string(ct.apifile)
		errormsg.msg = "Error reading the openEO API, neighter file nor url found"
		errormsg.output = string(err.Error())
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
		resp, errResp := client.Do(httpReq)

		if errResp != nil {
			errormsg := new(ErrorMessage)
			errormsg.input = string(ct.backend.url + ct.authendpoint)
			errormsg.msg = "Error calling the authentication url"
			errormsg.output = string(errResp.Error())
			return "Error1.5", errormsg

		} else if resp.StatusCode == 200 {
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
		errormsg.input = "Endpoint " + string(endpoint.Url) + " with token " + string(token)
		errormsg.msg = "Error processing the Config file"
		errormsg.output = string(errReq)
		return "Invalid", errormsg
	}

	// Find route in openAPI definition
	route, pathParams, err := router.FindRoute(httpReq.Method, httpReq.URL)

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.input = string(httpReq.Method) + "  " + string(endpoint.Url)
		errormsg.msg = "Error finding endpoint in the OpenAPI definition"
		errormsg.output = err.Error()
		return "Invalid", errormsg
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
		errormsg.input = string(httpReq.Method) + "  " + string(endpoint.Url)
		errormsg.msg = "Error validating the request"
		errormsg.output = string(err.Error())
		return "Invalid", errormsg
	}

	// Send request
	client := &http.Client{}

	execReq, errReq := ct.buildRequest(endpoint, token, true)

	resp, err := client.Do(execReq)

	if err != nil {
		errormsg := new(ErrorMessage)
		errormsg.input = string(httpReq.Method) + "  " + string(endpoint.Url)
		errormsg.msg = "Error sending request to back end"
		errormsg.output = string(err.Error())
		return "Invalid", errormsg
	}

	// Get Response
	body, err := ioutil.ReadAll(resp.Body)

	// log.Println(string(body))

	if resp.StatusCode == 401 {
		errormsg := new(ErrorMessage)
		errormsg.input = "Header Auth: " + execReq.Header.Get("Authorization")
		errormsg.msg = "Error: Authentication failed, currently only BasicAuth is supported."
		buf := new(bytes.Buffer)
		buf.ReadFrom(resp.Body)
		errormsg.output = buf.String()
		return "Invalid", errormsg
	}

	if err != nil {
		errormsg := new(ErrorMessage)
		buf := new(bytes.Buffer)
		buf.ReadFrom(resp.Body)
		//errormsg.input = "Response body: " + buf.String()
		errormsg.msg = "Error reading response from the back end"
		errormsg.output = string(err.Error())
		return "Invalid", errormsg
	}

	if resp.StatusCode == 404 {
		errormsg := new(ErrorMessage)
		errormsg.input = endpoint.Url
		errormsg.msg = "Endpoint was not found"
		errormsg.output = "Response Code " + strconv.Itoa(resp.StatusCode)
		return "Missing", errormsg
	} else if resp.StatusCode >= 400 && resp.StatusCode < 600 {
		errormsg := new(ErrorMessage)
		errormsg.input = endpoint.Url
		errormsg.msg = "An client or server error occured!"
		errormsg.output = "Response Code " + strconv.Itoa(resp.StatusCode)
		return "Error", errormsg
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
		//errormsg.input = "Response Body: " + string(body)
		errormsg.msg = "Response of the back end not valid"
		errormsg.output = err.Error()
		return "Invalid", errormsg
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

// Reads info from config file
func ReturnConfigValue(config_item string) string {
	var config_value = config_item
	if strings.HasPrefix(config_value, "$") {
		env_var := strings.Replace(config_value, "$", "", 1)
		config_value = os.Getenv(env_var)
		if len(config_value) == 0 {
			log.Println("Warning: Environment variable does not exist or is empty:", string(env_var))
			log.Println("Warning: Used raw input instead:", string(config_item))
			return config_item
		}
	}
	return config_value
}

// Main function
func main() {

	// Config file path
	var config Config

	// CLI handling
	app := cli.NewApp()
	app.Name = "openeoct"
	app.Name = "openeoct"
	app.Version = "1.0.0"
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
	// config = ReadConfig("examples/eodc_config_v1_0.toml") //"examples/gee_config_v1_0_0_external.toml")

	// config file read correctly
	if config.Url == "" {
		log.Println("Error: No config file specified")
	}

	// config = ReadConfig("examples/gee_config_v1_0_0_external.toml")
	// define back end and compliance test instance
	ct := new(ComplianceTest)

	ct.backend.url = ReturnConfigValue(config.Url)
	ct.apifile = ReturnConfigValue(config.Openapi)

	ct.username = ReturnConfigValue(config.Username)
	ct.password = ReturnConfigValue(config.Password)
	// ct.authendpoint = ReturnConfigValue(config.Authurl)

	if config.Authurl == "" {
		ct.authendpoint = "/credentials/basic"
	} else {
		ct.authendpoint = ReturnConfigValue(config.Authurl)
	}

	var ep_groups map[string][]Endpoint
	ep_groups = make(map[string][]Endpoint)
	for name, ep := range config.Endpoints {
		//log.Println("Ep:", string(ep))
		if ep.Id == "" {
			ep.Id = name
		}

		if ep.Group == "" {
			ep.Group = "nogroup"
		}

		ep_groups[ep.Group] = append(ep_groups[ep.Group], ep)
	}

	ct.endpoints = ep_groups

	// Run validation
	result := ct.validateAll()

	var result_json map[string](map[string]interface{})
	result_json = make(map[string](map[string]interface{}))

	for group, endpoints := range ep_groups {
		for _, ep := range endpoints {
			if result_json[group] == nil {
				result_json[group] = make(map[string]interface{})
				result_json[group]["group_summary"] = "Valid"
				result_json[group]["endpoints"] = make(map[string](map[string]string))
			}
			result_json[group]["endpoints"].(map[string](map[string]string))[ep.Url] = result[ep.Id]
			if result[ep.Id]["state"] != "Valid" && result[ep.Id]["state"] != "Missing" {
				result_json[group]["group_summary"] = "Invalid"
			}
		}
	}

	jsonString, _ := json.MarshalIndent(result_json, "", "    ")

	output := ReturnConfigValue(config.Output)

	// Write to log stdout or to output file
	if output == "" {
		log.Println(string(jsonString))
	} else {
		ioutil.WriteFile(output, jsonString, 0644)
	}

}
