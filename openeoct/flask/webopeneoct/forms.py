from wtforms import Form, BooleanField, StringField, PasswordField, validators, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired
from wtforms.widgets import PasswordInput
from .models import Backend, Endpoint, Config
import os


# class BackendForm(Form):
#     """
#     Form for the backend entity. Used to edit a backend instance.
#     """
#     id = IntegerField('Id')
#     name = StringField('Name')
#
#     def set_backend(self, backend):
#         """
#         Sets the form values to the values of an backend instance
#
#         Parameters
#         ----------
#         backend : Backend
#             Source backend instance
#         """
#         self.name.data = backend.name
#         self.id.data = backend.id
#
#     def get_config(self):
#         """
#            Get config instance with the data of the form instance.
#
#            Return
#            ----------
#            backend : Backend
#                Backend instance with values of the form.
#         """
#         return Backend(self.id.data, self.name.data)


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
    version = StringField('Backend-version')
    openapi = StringField('OpenAPI-URL') #SelectField('Backend', choices=[('0_3_1', '0.3.1'), ('0_4_0', '0.4.0'), ('0_4_1', '0.4.1')])
    # output = StringField('Output')
    # authurl = StringField('Authentication URL')
    username = StringField('Authentication Username')
    password = StringField('Authentication Password', widget=PasswordInput(hide_value=False))

    def set_backend(self, backend):
        """
        Sets the form values to the values of an backend instance

        Parameters
        ----------
        config : Backend
            Source backend instance
        """
        self.name.data = backend.name
        self.id.data = backend.id
        for config in backend.configs:
            if config.url:
                self.url.data = config.url
            if config.version:
                self.version.data = config.version
            if config.password:
                self.password.data = config.password
            if config.username:
                self.username.data = config.username
            # self.output.data = backend.output
            if config.openapi:
                self.openapi.data = config.openapi

    def get_backend(self):
        """
           Get backend instance with the data of the form instance.

           Return
           ----------
           backend : Backend
               Backend instance with values of the form.
        """
        # default_output = "result_{}.json".format(self.id.data)
        return Backend(self.id.data, self.name.data)


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
                                   DataRequired('Please select an organisation')])
    url = StringField('URL')
    type = SelectField('Request Method', choices=[('GET', 'GET'), ('POST', 'POST'), ('PATCH', 'PATCH'), ('PUT', 'PUT'),
                                        ('DELETE', 'DELETE')],
                               validators=[
                                   DataRequired('Please select an organisation')])
    body = TextAreaField('Body', render_kw={'class': 'form-control', 'rows': 20})

    optional = BooleanField("Optional")#SelectField('Optional', choices=[(False, "no"), (True, 'yes')])
    group = StringField('Group')
    timeout = IntegerField('Timeout')
    order = IntegerField('Order')

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
        self.id.data = endpoint.id

        body_file = "body_{}".format(self.id.data)
        if os.path.isfile(body_file):
            f = open(body_file, "r")
            self.body.data = f.read()
            f.close()

    def get_endpoint(self):
        """
           Get endpoint instance with the data of the form instance.

           Return
           ----------
           endpoint : Endpoint
               Endpoint instance with values of the form.
        """
        return Endpoint(self.backend.data, self.url.data, self.type.data, optional=self.optional.data,
                        group=self.group.data, timeout=self.timeout.data, order=self.order.data)
        #body=self.body.data, head=self.head.data, #auth=self.auth.data)
