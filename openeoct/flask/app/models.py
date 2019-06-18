from app import db


class Backend(db.Model):
    """
    Backend class that contains all information related to a backend,
    including a many-to-one relation to the Endpoint instance.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    url = db.Column(db.String, nullable=False)
    openapi = db.Column(db.String, nullable=False)
    output = db.Column(db.String)
    authurl = db.Column(db.String)
    username = db.Column(db.String)
    password = db.Column(db.String)

    endpoints = db.relationship("Endpoint", lazy="dynamic")

    def __init__(self, id, name, url, openapi, output=None, authurl=None, username=None, password=None):
        self.id = id
        self.name = name
        self.url = url
        self.openapi = openapi
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


class Endpoint(db.Model):
    """
    Endpoint class that contains all information related to an endpoint,
    including a one-to-many relation to the Backend instance.
    """
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, unique=True, nullable=False)
    type = db.Column(db.String, nullable=False)
    body = db.Column(db.String)
    head = db.Column(db.String)
    auth = db.Column(db.String)

    backend = db.Column(db.Integer, db.ForeignKey('backend.id'))

    def __init__(self, backend, url, type, body=None, head=None, auth=None):
        self.backend = backend
        self.url = url
        self.type = type
        self.body = body
        self.head = head
        self.auth = auth

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


class Result():
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

