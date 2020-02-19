from .models import Backend, Endpoint, Result
from openeoct.flask.webopeneoct import db
import json
import toml
import subprocess
import os
import time
from shutil import copyfile
import requests

WORKING_DIR = "../.."
PYTEST_DIR = "../../../openeo_compliance_tests/"
PYTEST_CMD = "/home/bgoesswe/.pyenv/versions/miniconda3-latest/envs/openeoct/bin/pytest"


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

    endpoint_list = {}
    counter = 0
    for endpoint in endpoints:
        endpoint_list["endpoints.endpoint"+str(counter)] = {
            "id": "endpoint"+str(counter),
            "url": endpoint.url,
            "request_type": endpoint.type
        }



        body_file = "body_{}".format(endpoint.id)
        if os.path.isfile(body_file):
            body_full_path = os.getcwd() + "/" + body_file
            endpoint_list["endpoints.endpoint" + str(counter)]["body"] = body_full_path

        counter += 1

    #openapi_file = "openapi_{}.json".format(backend.openapi)

    if backend.output == "result_None.json":
        backend.output = "result_{}.json".format(be_id)
        db.session.commit()

    toml_dict = {
        "url": backend.url,
        "openapi": backend.openapi,
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


def common_member(a, b):
    a_set = set(a)
    b_set = set(b)
    if len(a_set.intersection(b_set)) > 0:
        return(True)
    return(False)


def gen_endpoints(be_id, re_types=["GET"], leave_ids=True):
    """
    Generates an endpoint in the config file for each endpoint listed in the capabilities page of the backend.
    If an endpoint does already exists, it is not overwritten but ignored.

    Parameters
    ----------
    be_id : int
        ID of Backend

    Return
    ----------
    result_list : list
        List of Endpoint instances that have been added, empty if no endpoint was added.
    """
    ep_list = []
    backend = Backend.query.filter(Backend.id == be_id).first()

    if not backend:
        return []

    resp = requests.get(backend.url)
    capabilities = resp.json()

    endpoints = Endpoint.query.filter(Endpoint.backend == be_id).all()
    url_dict = {}


    # Existing endpoint urls of the backend
    for ep in endpoints:
        if ep.url in url_dict:
            url_dict[ep.url].append(ep.type)
        else:
            url_dict[ep.url] = [ep.type]

    for ep in capabilities["endpoints"]:

        if "methods" in ep:
            if not common_member(re_types, ep["methods"]):
                continue

        if "path" in ep:

            if leave_ids:
                if "{" in ep["path"]:
                    continue
            for met in ep["methods"]:

                if met not in re_types:
                    continue
                if ep["path"] in url_dict:
                    if met in url_dict[ep["path"]]:
                        continue

                new_ep = Endpoint(be_id, ep["path"], met)

                db.session.add(new_ep)
                db.session.commit()
                ep_list.append(new_ep)
                print(ep)

    create_configfile(be_id)
    return ep_list


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
    time.sleep(1)
    backend = Backend.query.filter(Backend.id == be_id).first()

    if backend.output == "result_None.json":
        backend.output = "result_{}.json".format(backend.id)
        db.session.commit()

    result_path = "{}/{}".format(WORKING_DIR, backend.output)

    if os.path.isfile(result_path):
        result_file = open("{}/{}".format(WORKING_DIR, backend.output), "r")

        result = json.loads(result_file.read())

        result_list = []

        for key, val in result.items():
            result_list.append(Result(key, val))

        return result_list
    return None


def run_validation(be_id):
    """
    Run validation of backend. First recreates the config file and then executes the configuration.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    # config_path = create_configfile(be_id)

    config_path = "config_{}.toml".format(str(be_id))

    config_path = os.getcwd() + "/" + config_path

    cmd = ['./openeoct', 'config', config_path]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=WORKING_DIR)

    out, err = p.communicate()
    print(err)
    if len(err) != 0:
        return ["Error executing the openeoct command"]

    return read_result(be_id)


def run_pytest_validation(be_id):

    backend = Backend.query.filter(Backend.id == be_id).first()

    #cmd = [PYTEST_CMD, '--backend', backend.url, '--html', 'report_{}.html'.format(be_id)]
    #cmd = ['ls']
    api_version = "0.4.2"
    cmd = "{} --backend {} " \
          "--html report_{}.html --api-version {}".format(PYTEST_CMD, backend.url, be_id, api_version)
    #print(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=PYTEST_DIR, shell=True)
    #py.test.cmdline.main(["--backend {}".format(backend.url), "--html report_{}.html".format(be_id)])
    #pytest.main()

    out, err = p.communicate()
    print("Error: {}".format(err))
    print("Output: {}".format(out))
    if len(err) != 0:
        return None

    copyfile(get_pytest_path(be_id), get_pytest_static_path(be_id))

    return "report_{}.html".format(be_id)


def get_pytest_path(be_id):

    result_path = os.path.join(PYTEST_DIR, "report_{}.html".format(be_id))
    result_path = os.path.abspath(result_path)
    if os.path.isfile(result_path):
        return result_path
    else:
        return None


def get_pytest_static_path(be_id):
    result_path = os.path.abspath("static/report_{}.html".format(be_id))
    #result_path = os.path.join(PYTEST_DIR, "static/report_{}.html".format(be_id))
    #result_path = os.path.abspath(result_path)
    return result_path
