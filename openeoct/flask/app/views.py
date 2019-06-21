
from app import app, db
from .forms import BackendForm, EndpointForm
from flask import request, flash, redirect, url_for, render_template
from .models import Backend, Endpoint
from .service import run_validation

CONFIG_PATH = "gee_config.toml"


@app.route('/')
def home():
    """
    Home - Site of openeoct, listing the backends and linking to the validation and edit pages.
    """
    backends = Backend.query.all()

    return render_template('home.html', backends=backends)


@app.route('/backend/edit/<be_id>', methods=['GET', 'POST'])
def backend_edit(be_id):
    """
    Edit or register a backend at the database. If be_id is not None it will edit the existing one,
    otherwise it creates a new backend instance.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    form = BackendForm(request.form)

    if request.method == 'POST' and form.validate():

        backend = form.get_backend()

        orig_backend = Backend.query.filter(Backend.id == be_id).first()

        if not orig_backend:
            db.session.add(backend)
        else:
            orig_backend.set(backend)
            db.session.commit()
        return redirect(url_for('home'))
    else:
        if be_id:
            backend = Backend.query.filter(Backend.id == be_id).first()
            if backend:
                form.set_backend(backend)

    endpoints = None
    if be_id:
        endpoints = Endpoint.query.filter(Endpoint.backend == be_id).all()

    return render_template('backend_edit.html', form=form, endpoints=endpoints)


@app.route('/backend/register/', methods=['GET', 'POST'])
def backend_register():
    """
    Edit or register a backend at the database. If be_id is not None it will edit the existing one,
    otherwise it creates a new backend instance.

    """
    form = BackendForm(request.form)

    if request.method == 'POST' and form.validate():

        backend = form.get_backend()

        db.session.add(backend)

        return redirect(url_for('home'))

    return render_template('backend_register.html', form=form, endpoints=None)


@app.route('/endpoint/register', methods=['GET', 'POST'], defaults={'ep_id': None})
@app.route('/endpoint/register/<ep_id>', methods=['GET', 'POST'])
def endpoint_register(ep_id=None):
    """
    Edit or register an endpoint at the database. If ep_id is not None it will edit the existing one,
    otherwise it creates a new enpoint instance.

    Parameters
    ----------
    ep_id : int
        ID of endpoint
    """
    form = EndpointForm(request.form)
    if request.method == 'POST' and form.validate():

        endpoint = form.get_endpoint()

        orig_endpoint = Endpoint.query.filter(Endpoint.id == ep_id).first()

        if not orig_endpoint:
            db.session.add(endpoint)
        else:
            orig_endpoint.set(endpoint)
            db.session.commit()

        return redirect(url_for('backend_edit', be_id=endpoint.backend))
    else:
        if ep_id:
            endpoint = Endpoint.query.filter(Endpoint.id == ep_id).first()
            if endpoint:
                form.set_endpoint(endpoint)

    return render_template('endpoint_register.html', form=form)


@app.route('/backend/add/<be_id>', methods=['GET', 'POST'])
def backend_add_endpoint(be_id=None):
    """
    Add an endpoint to a backend at the database.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    form = EndpointForm(request.form)

    if request.method == 'POST' and form.validate():

        endpoint = form.get_endpoint()
        db.session.add(endpoint)

        return redirect(url_for('backend_edit', be_id=endpoint.backend))
    else:
        form.backend.data = be_id

    return render_template('endpoint_register.html', form=form)


@app.route('/backend/validate/<be_id>')
def backend_validate(be_id):
    """
    Validates all endpoints of a backend.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    backend = Backend.query.filter(Backend.id == be_id).first()

    form = BackendForm(request.form)

    form.set_backend(backend)

    results = run_validation(be_id)

    return render_template('backend_validate.html', form=form, results=results)

@app.route('/endpoint/list')
@app.route('/endpoint/list/<be_id>')
def endpoint_list(be_id=None):
    """
    Lists all endpoints, if be_id is not None it will only list the endpoints related to the specific backend.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    if not be_id:
        endpoints = Endpoint.query.all()
    else:
        endpoints = Endpoint.query.filter(Endpoint.backend == be_id).all()

    return render_template('endpoint_list.html', endpoints=endpoints)