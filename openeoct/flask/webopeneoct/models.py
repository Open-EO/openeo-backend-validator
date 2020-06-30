from openeoct.flask.webopeneoct import db
import requests
import os


class Backend(db.Model):
    """
    Backend class that contains all information related to a backend,
    including a many-to-one relation to the Endpoint instance.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    url = db.Column(db.String, nullable=False)
    version = db.Column(db.String)
    openapi = db.Column(db.String, nullable=False)
    output = db.Column(db.String)
    authurl = db.Column(db.String)
    username = db.Column(db.String)
    password = db.Column(db.String)

    endpoints = db.relationship("Endpoint", lazy="dynamic")
    variables = db.relationship("Variable", lazy="dynamic")

    def __init__(self, id, name, url, openapi, output=None, authurl=None, username=None, password=None, version=None):
        self.id = id
        self.name = name
        self.url = url
        self.openapi = openapi

        self.version = version
        self.output = output
        self.authurl = authurl
        self.username = username
        self.password = password

    def set(self, backend):
        """
        Sets the backend to the given backend instance, except for the id.

        Parameters
        ----------
        backend : Backend
           Backend instance

        """
        self.name = backend.name
        self.url = backend.url
        self.openapi = backend.openapi
        self.output = backend.output
        self.authurl = backend.authurl
        self.username = backend.username
        self.password = backend.password

    def get_url(self):
        if not self.version:
            return self.url

        resp = requests.get(self.url + "/.well-known/openeo")
        versions = resp.json()

        for version in versions.get("versions"):
            if version.get("api_version") == self.version:
                return version.get("url")

        return self.url

    def to_json(self):
        endpoint_list = {}
        for endpoint in self.endpoints:
            endpoint_list["endpoints." + str(endpoint.id)] = endpoint.to_json()

        variables_list = {}
        for variable in self.variables:
            variables_list[variable.name] = variable.value

        if self.output == "result_None.json":
            self.output = "result_{}.json".format(self.id)
            db.session.commit()

        json_dict = {
            "url": self.url,
            "openapi": self.openapi,
            "username": self.username,
            "password": self.password,
            "endpoints": endpoint_list,
            "output": self.output
        }

        if variables_list:
            json_dict["variables"] = variables_list
        if self.version:
            json_dict["backendversion"] = self.version
        if self.authurl:
            json_dict["authurl"] = self.authurl

        return json_dict


class Variable(db.Model):
    """
    Class that contains variables
    including a many-to-one relation to the backend instance.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    value = db.Column(db.String)

    backend = db.Column(db.Integer, db.ForeignKey('backend.id'))

    def __init__(self, name, value, backend=None):
        self.name = name
        self.value = value
        if backend:
            self.backend = backend


class Endpoint(db.Model):
    """
    Endpoint class that contains all information related to an endpoint,
    including a one-to-many relation to the Backend instance.
    """
    id = db.Column(db.String, primary_key=True)
    url = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    body = db.Column(db.String)
    head = db.Column(db.String)
    auth = db.Column(db.String)
    optional = db.Column(db.Boolean)
    group = db.Column(db.String, primary_key=True)
    timeout = db.Column(db.Integer)
    order = db.Column(db.Integer)

    backend = db.Column(db.Integer, db.ForeignKey('backend.id'))

    def __init__(self, backend, url, type, body=None, head=None, auth=None, optional=False,
                 group="nogroup", timeout=None, order=None):
        self.backend = backend
        self.url = url
        self.type = type
        self.body = body
        self.head = head
        self.auth = auth
        self.optional = optional
        self.group = group
        self.timeout = timeout
        self.order = order

    def set(self, endpoint):
        """
            Sets the endpoint to the given endpoint instance, except for the id.
            Parameters
            ----------
            endpoint : Endpoint
                Endpoint instance
        """
        self.url = endpoint.url
        self.type = endpoint.type
        self.body = endpoint.body
        self.head = endpoint.head
        self.auth = endpoint.auth
        self.optional = endpoint.optional
        self.group = endpoint.group
        self.timeout = endpoint.timeout
        self.order = endpoint.order

    def to_json(self):
        endpoint_dict = {
            "url": self.url,
            "request_type": self.type
        }
        if self.order:
            endpoint_dict["order"] = self.order
        if self.timeout:
            endpoint_dict["timeout"] = self.timeout
        if self.group:
            endpoint_dict["group"] = self.group
        if self.optional:
            endpoint_dict["optional"] = self.optional

        body_file = "body_{}".format(self.id)
        if os.path.isfile(body_file):
            body_full_path = os.getcwd() + "/" + body_file
            endpoint_dict["endpoints." + str(self.id)]["body"] = body_full_path

        return endpoint_dict


class Result:
    """
    Result class that contains all information related to an result of an validation.
    """
    endpoint = None
    value = {}
    success = False

    def __init__(self, endpoint, value, success=None):
        self.endpoint = endpoint
        self.value = value

        if success:
            self.success = success
        else:
            if value == "Valid":
                self.success = True
            else:
                self.success = False

