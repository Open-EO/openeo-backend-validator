from .models import Backend, Endpoint, Result
import json
import toml
import subprocess
import os


def create_configfile(be_id):
    """
    Creates the toml config file for the openeoct tool, according to the config stored in the database.

    Parameters
    ----------
    be_id : int
        ID of Backend

    Return
    ----------
    config_path : String
        Path of the created config file.

    """
    backend = Backend.query.filter(Backend.id == be_id).first()

    endpoints = Endpoint.query.filter(Endpoint.backend == be_id).all()

    config_path = "config_{}.toml".format(str(backend.id))

    endpoint_list = []

    for endpoint in endpoints:
        endpoint_list.append(endpoint.url)

    openapi_file = "openapi_{}.json".format(backend.openapi)

    toml_dict = {
        "url": backend.url,
        "openapi": openapi_file,
        "username": backend.username,
        "password": backend.password,
        "authurl": backend.authurl,
        "endpoints": endpoint_list,
        "output": backend.output
    }

    new_toml_string = toml.dumps(toml_dict)
    print(new_toml_string)
    with open(config_path, "w") as text_file:
        text_file.write(new_toml_string)

    return config_path


def read_result(be_id):
    """
    Reads the results of the validation process from the output file.

    Parameters
    ----------
    be_id : int
        ID of Backend

    Return
    ----------
    result_list : list
        List of Result instances.

    """
    backend = Backend.query.filter(Backend.id == be_id).first()

    result_file = open("../{}".format(backend.output), "r")

    result = json.loads(result_file.read())

    result_list = []

    for key, val in result.items():
        result_list.append(Result(key, val))

    return result_list


def run_validation(be_id):
    """
    Run validation of backend. First recreates the config file and then executes the configuration.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    config_path = create_configfile(be_id)

    config_path = os.getcwd() + "/" + config_path

    cmd = ['./openeoct', 'config', config_path]

    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="..")

    return read_result(be_id)



