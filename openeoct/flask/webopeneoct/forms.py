from wtforms import Form, BooleanField, StringField, PasswordField, validators, SelectField, TextAreaField, IntegerField
from wtforms.validators import Required
from .models import Backend, Endpoint


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
    openapi = SelectField('Backend', choices=[('0_3_1', '0.3.1'), ('0_4_0', '0.4.0'), ('0_4_1', '0.4.1')])
    output = StringField('Output')
    authurl = StringField('Authentication URL')
    username = StringField('Authentication Username')
    password = StringField('Authentication Password')

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
        self.authurl.data = backend.authurl
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
                authurl=self.authurl.data, username=self.username.data, password=self.password.data)


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
    id = IntegerField('Id')
    backend = SelectField('Backend', coerce=int,
                               validators=[
                                   Required('Please select an organisation')])
    url = StringField('URL')
    type = SelectField('Type', choices=[('get', 'GET')],#, ('post', 'POST'), ('patch', 'PATCH')],
                               validators=[
                                   Required('Please select an organisation')])
#    body = TextAreaField('Body')
#    head = TextAreaField('Head')
#    auth = SelectField('Authentication', choices=[('Auto', 'auto'), ('Yes', 'yes'), ('No', 'no')])

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
#        self.body.data = endpoint.body
#        self.head.data = endpoint.head
#        self.auth.data = endpoint.auth
        self.id.data = endpoint.id

    def get_endpoint(self):
        """
           Get endpoint instance with the data of the form instance.

           Return
           ----------
           endpoint : Endpoint
               Endpoint instance with values of the form.
        """
        return Endpoint(self.backend.data, self.url.data, self.type.data) #body=self.body.data, head=self.head.data,
                #auth=self.auth.data)