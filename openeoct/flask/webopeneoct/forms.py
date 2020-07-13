from wtforms import Form, BooleanField, StringField, PasswordField, validators, SelectField, \
                    TextAreaField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired
from wtforms.widgets import PasswordInput
from .models import Backend, Endpoint, Variable
from .service import BodyHandler
import os


class VariableForm(Form):
    """
    Form for the endpoint entity. Used to edit an endpoint instance.
    """
    id = IntegerField('Id')
    name = StringField('Name')
    value = StringField('Value')
    backend = SelectField('Backend', coerce=int,
                               validators=[
                                   DataRequired('Please select a backend')])

    def __init__(self, *args, **kwargs):
        """
            Constructor of the EndpointForm. Creates the backend list according to the entities of the database.

        """
        super(VariableForm, self).__init__(*args, **kwargs)
        backends = Backend.query.with_entities(
            Backend.id, Backend.name). \
            order_by(Backend.name).all()
        self.backend.choices = [
            (backend.id, backend.name)
            for backend in backends
        ]

    def set_variable(self, variable):

        self.id.data = variable.id
        self.name.data = variable.name
        self.value.data = variable.value
        self.backend.data = variable.backend

    def get_variable(self):
        variable = Variable(name=self.name.data, value=self.value.data, backend=self.backend.data)
        if self.id.data:
            variable.id = self.id.data
        return variable


class BackendForm(Form):
    """
    Form for the backend entity. Used to edit a backend instance.

    Attributes
    ----------
    id : IntegerField
        ID of backend
    name : StringField
        Name of backend
    url : StringField
        URL of backend
    openapi : StringField
        Core openEO API version of backend
    output : StringField
        Outputfile of the validation of backend
    authurl : StringField
        Authentication URL of backend
    username : StringField
        Authentication Username of backend
    password : StringField
        Authentication Password of backend
    """
    id = IntegerField('Id')
    name = StringField('Name')
    url = StringField('URL')
    openapi = StringField('OpenAPI-URL') #SelectField('Backend', choices=[('0_3_1', '0.3.1'), ('0_4_0', '0.4.0'), ('0_4_1', '0.4.1')])
    output = StringField('Output')
    version = StringField('Backend-Version')
    authurl = StringField('Authentication URL')
    username = StringField('Authentication Username')
    password = StringField('Authentication Password', widget=PasswordInput(hide_value=False))

    # variables = FieldList(FormField(VariableForm))

    def set_backend(self, backend):
        """
        Sets the form values to the values of an backend instance

        Parameters
        ----------
        backend : Backend
            Source backend instance
        """
        self.name.data = backend.name
        self.url.data = backend.url
        # self.authurl.data = backend.authurl
        self.version.data = backend.version
        self.password.data = backend.password
        self.username.data = backend.username
        self.output.data = backend.output
        self.openapi.data = backend.openapi
        self.id.data = backend.id

    def get_backend(self):
        """
           Get backend instance with the data of the form instance.

           Return
           ----------
           backend : Backend
               Backend instance with values of the form.
        """
        default_output = "result_{}.json".format(self.id.data)
        return Backend(self.id.data, self.name.data, self.url.data, self.openapi.data, output=default_output,
                       username=self.username.data, version=self.version.data, password=self.password.data)


class EndpointForm(Form):
    """
    Form for the endpoint entity. Used to edit an endpoint instance.

    Attributes
    ----------
    id : IntegerField
        ID of endpoint
    backend : SelectField
        Backend related to the endpoint
    url : StringField
        URL of endpoint
    type : SelectField
        REST type of the endpoint
    body : TextAreaField
        Body of the endpoint
    head : TextAreaField
        Head of the endpoint
    auth : SelectField
        Set if authentication has to be used or not for the endpoint ('auto' to set it according to the specification)
    """
    id = StringField('Id')
    backend = SelectField('Backend', coerce=int,
                               validators=[
                                   DataRequired('Please select a backend')])
    url = StringField('URL')
    type = SelectField('Type', choices=[('GET', 'GET'), ('POST', 'POST'), ('PATCH', 'PATCH'), ('PUT', 'PUT'),
                                        ('DELETE', 'DELETE')],
                               validators=[
                                   DataRequired('Please select a http method  / type')])
    body = TextAreaField('Body', render_kw={'class': 'form-control', 'rows': 20})
    optional = BooleanField("Optional")#SelectField('Optional', choices=[(False, "no"), (True, 'yes')])
    group = StringField('Group')
    timeout = IntegerField('Timeout')
    order = IntegerField('Order')
    wait = IntegerField('Seconds to wait after endpoint validation')
    retry = StringField('Retry validation as long as openEO error code occurs (e.g. JobNotFinished)')

    def __init__(self, *args, **kwargs):
        """
            Constructor of the EndpointForm. Creates the backend list according to the entities of the database.

        """
        super(EndpointForm, self).__init__(*args, **kwargs)
        backends = Backend.query.with_entities(
            Backend.id, Backend.name). \
            order_by(Backend.name).all()
        self.backend.choices = [
            (backend.id, backend.name)
            for backend in backends
        ]

    def set_endpoint(self, endpoint):
        """
            Sets the form values to the values of an endpoint instance

            Parameters
            ----------
            endpoint : Endpoint
                Source endpoint instance
        """
        self.backend.data = endpoint.backend
        self.url.data = endpoint.url
        self.type.data = endpoint.type
        # self.body.data = endpoint.body
        self.optional.data = endpoint.optional
        #if endpoint.optional:
        #    self.optional.data = (True, "yes")
        #else:
        #    self.optional.data = (False, "no")
        if not endpoint.group:
            self.group.data = "nogroup"
        else:
            self.group.data = endpoint.group

        if not endpoint.timeout:
            self.timeout.data = 0
        else:
            self.timeout.data = endpoint.timeout
        if not endpoint.order:
            self.order.data = 0
        else:
            self.order.data = endpoint.order
        if not endpoint.wait:
            self.wait.data = 0
        else:
            self.wait.data = endpoint.wait
        if not endpoint.retry:
            self.retry.data = ""
        else:
            self.retry.data = endpoint.retry

        self.id.data = endpoint.id

        if endpoint.body:
            body_handler = BodyHandler()
            self.body.data = body_handler.read_body(endpoint.body)

        # body_file = "body_{}".format(self.id.data)
        # if os.path.isfile(body_file):
        #     f = open(body_file, "r")
        #     self.body.data = f.read()
        #     f.close()

    def get_endpoint(self):
        """
           Get endpoint instance with the data of the form instance.

           Return
           ----------
           endpoint : Endpoint
               Endpoint instance with values of the form.
        """
        ep = Endpoint(self.backend.data, self.url.data, self.type.data, optional=self.optional.data,
                 group=self.group.data, timeout=self.timeout.data, order=self.order.data, id=self.id.data,
                 wait=self.wait.data, retry=self.retry.data)
        if self.body.data:
            ep.body = "body_{}_{}".format(str(self.backend.data), self.id.data)
        return ep