
from openeoct.flask.webopeneoct import app, db
from flask import request, flash, redirect, url_for, render_template, send_file
from .forms import BackendForm, EndpointForm, VariableForm
from .models import Backend, Endpoint, Variable
from .service import run_validation, create_configfile, run_pytest_validation, gen_endpoints, \
    configs_to_backend, read_configfile, BodyHandler, read_file, write_configfile, write_file, run_validation_deliverable
import os
from werkzeug import secure_filename


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

        #create_configfile(be_id)

        return redirect(request.referrer)
    else:
        if be_id:
            backend = Backend.query.filter(Backend.id == be_id).first()
            if backend:
                form.set_backend(backend)

    endpoints = None
    if be_id:
        endpoints = Endpoint.query.filter(Endpoint.backend == be_id).all()

    variables = None
    if be_id:
        variables = Variable.query.filter(Variable.backend == be_id).all()

    return render_template('backend_edit.html', form=form, endpoints=endpoints, variables=variables)


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


@app.route('/backend/registercfg/', methods=['GET', 'POST'])
@app.route('/backend/registercfg/<be_id>', methods=['GET', 'POST'])
def backend_register_cfg(be_id=None):

    name = ""
    backend = None

    if be_id:
        backend = Backend.query.filter(Backend.id == be_id).first()
        name = backend.name

    if request.method == 'POST':

        name = ""
        if "name" in request.form:
            name = request.form["name"]

        if not backend and name:
            ba = Backend.query.filter(Backend.name == name).first()
            if ba:
                return render_template('backend_config_upload.html', name=name,
                                       warning_message="Error backend name already exists!")

        file_list = request.files.getlist("file")

        file_paths = []

        for f in file_list:
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            file_paths.append(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))

        if backend:
            if name:
                backend.name = name
            for file in file_paths:
                config_json = read_configfile(file)
                backend.append_config(config_json)
        else:
            configs_to_backend(file_paths=file_paths, name=name)

        db.session.commit()
        if be_id:
            return redirect(request.referrer)
        else:
            return redirect(url_for('home'))
    return render_template('backend_config_upload.html', name=name, warning_message=None)


@app.route('/backend/gen_get_endpoints/<be_id>', methods=['GET'])
def backend_gen_get_endpoints(be_id):
    """
    Generates an endpoint in the config file for each endpoint listed in the capabilities page of the backend.
    If an endpoint does already exists, it is not overwritten but ignored.
    """
    try:
        gen_endpoints(be_id)
    except:
        if be_id:
            form = BackendForm(request.form)
            backend = Backend.query.filter(Backend.id == be_id).first()
            if backend:
                form.set_backend(backend)
        endpoints = None
        if be_id:
            endpoints = Endpoint.query.filter(Endpoint.backend == be_id).all()

        variables = None
        if be_id:
            variables = Variable.query.filter(Variable.backend == be_id).all()
        return render_template('backend_edit.html', form=form, endpoints=endpoints, variables=variables,
                               warning_message="Could not create GET endpoints, maybe URL is not valid!")

    return redirect(url_for('backend_edit', be_id=be_id))


@app.route('/backend/gen_all_endpoints/<be_id>', methods=['GET'])
def backend_gen_all_endpoints(be_id):
    """
    Generates an endpoint in the config file for each endpoint listed in the capabilities page of the backend.
    If an endpoint does already exists, it is not overwritten but ignored.
    """
    try:
        gen_endpoints(be_id, re_types=["GET", "POST", "PUT", "DELETE", "PATCH"], leave_ids=False)
    except:
        if be_id:
            form = BackendForm(request.form)
            backend = Backend.query.filter(Backend.id == be_id).first()
            if backend:
                form.set_backend(backend)
        endpoints = None
        if be_id:
            endpoints = Endpoint.query.filter(Endpoint.backend == be_id).all()

        variables = None
        if be_id:
            variables = Variable.query.filter(Variable.backend == be_id).all()
        return render_template('backend_edit.html', form=form, endpoints=endpoints, variables=variables,
                               warning_message="Could not create ALL endpoints, maybe URL is not valid!")

    return redirect(url_for('backend_edit', be_id=be_id))


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
        body_handler = BodyHandler()

        endpoint = form.get_endpoint()
        if 'file' in request.files:
            file = request.files['file']
            filename = secure_filename(file.filename)
            if filename:
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(full_path)
                body_path = "body_{}_{}".format(str(endpoint.backend), ep_id)
                body_handler.transfer_body(full_path, body_path)
                form.body.data = body_handler.read_body(body_path)

        orig_endpoint = Endpoint.query.filter(Endpoint.id == ep_id).first()

        if not orig_endpoint:
            db.session.add(endpoint)
        else:
            orig_endpoint.set(endpoint)
            db.session.commit()

        if len(form.body.data) != 0:
            body_handler.write_body(value=form.body.data, name="body_{}_{}".format(str(endpoint.backend), ep_id))

        return redirect(request.referrer)
    else:
        if ep_id:
            endpoint = Endpoint.query.filter(Endpoint.id == ep_id).first()
    if endpoint:
        form.set_endpoint(endpoint)

    return render_template('endpoint_register.html', form=form)


@app.route('/endpoint/add/<be_id>', methods=['GET', 'POST'])
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

        if len(form.body.data) != 0:
            body_handler = BodyHandler()
            body_handler.write_body(value=form.body.data, name="body_{}_{}".format(str(endpoint.backend), endpoint.id))

        return redirect(request.referrer)
    else:
        form.backend.data = be_id

    return render_template('endpoint_register.html', form=form)


@app.route('/variable/add/<be_id>', methods=['GET', 'POST'])
def backend_add_variable(be_id=None):
    """
    Add an endpoint to a backend at the database.

    Parameters
    ----------
    be_id : int
        ID of backend
    """

    form = VariableForm(request.form)

    if request.method == 'POST' and form.validate():

        variable = form.get_variable()
        db.session.add(variable)

        #create_configfile(be_id)

        return redirect(request.referrer)
    else:
        form.backend.data = be_id

    return render_template('variable_register.html', form=form)


@app.route('/endpoint/del/<ep_id>', methods=['GET', 'POST'])
def backend_del_endpoint(ep_id=None):
    """
    Add an endpoint to a backend at the database.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    if ep_id:

        endpoint = Endpoint.query.filter(Endpoint.id == ep_id).first()
        #be_id = endpoint.backend
        db.session.delete(endpoint)
        db.session.commit()
        #create_configfile(be_id)

    return redirect(request.referrer)


@app.route('/variable/del/<va_id>', methods=['GET', 'POST'])
def backend_del_variable(va_id=None):

    if va_id:
        variable = Variable.query.filter(Variable.id == va_id).first()
        #be_id = variable.backend
        db.session.delete(variable)
        db.session.commit()
        #create_configfile(be_id)

    return redirect(request.referrer)


@app.route('/backend/del/<be_id>', methods=['GET', 'POST'])
def backend_delete(be_id=None):
    backend = Backend.query.filter(Backend.id == be_id).first()
    # be_id = variable.backend
    #db.session.delete(backend)
    backend.delete()
    db.session.commit()
    # create_configfile(be_id)
    return redirect(request.referrer)


@app.route('/backend/validate/deliverable/edit/<be_id>', methods=['GET', 'POST'])
def backend_validate_deliverable_edit(be_id):
    """
    Validates all endpoints of a backend.

    Parameters
    ----------
    be_id : int
        ID of backend
    """

    deliverable_path = app.config["D28_Folder"]
    deliverable_body_path = os.path.join(deliverable_path, "src", "openeo_d28", "body")
    job_filepath = os.path.join(deliverable_body_path, "job_file_{}".format(be_id))
    job_sync_filepath = os.path.join(deliverable_body_path, "job_sync_file_{}".format(be_id))
    udp_filepath = os.path.join(deliverable_body_path, "udp_file_{}".format(be_id))
    be_config_path = os.path.join(deliverable_path, "src", "openeo_d28", "D28_config_{}.toml".format(be_id))
    sample_config_path = os.path.join(deliverable_path, "src", "openeo_d28", "SAMPLE_config.toml")

    form = BackendForm(request.form)

    if request.method == 'POST':
        req_form = request.form
        req_files = request.files
        file = None
        if 'udp_file' in req_files:
            if req_files['udp_file'].filename != "":
                file = req_files['udp_file']
                file.save(udp_filepath)
        if not file:
            write_file(udp_filepath, req_form["udp"])

        file = None
        if 'job_file' in req_files:
            file = req_files['job_file']
            file.save(job_filepath)
        if not file:
            write_file(job_filepath, req_form["job"])

        file = None
        if 'job_sync_file' in req_files:
            file = req_files['job_sync_file']
            file.save(job_sync_filepath)
        if not file:
            write_file(job_sync_filepath, req_form["job_sync"])

        backend = form.get_backend()
        orig_backend = Backend.query.filter(Backend.id == be_id).first()

        if not orig_backend:
            db.session.add(backend)
        else:
            orig_backend.set(backend)
            db.session.commit()

        be_conf_json = read_configfile(sample_config_path)

        be_conf_json["url"] = backend.url
        be_conf_json["backendversion"] = backend.version
        be_conf_json["username"] = backend.username
        be_conf_json["password"] = backend.password
        be_conf_json["output"] = "result_{}.json".format(be_id)

        be_conf_json["variables"]["pg_filename"] = udp_filepath
        be_conf_json["variables"]["job_filename"] = job_filepath
        be_conf_json["variables"]["job_sync_filename"] = job_sync_filepath
        req_form = request.form

        if "udp_name" in req_form:
            be_conf_json["variables"]["process_graph_id"] = req_form["udp_name"]
        if "pre_job_id" in req_form:
            be_conf_json["variables"]["job_id_precomputed"] = req_form["pre_job_id"]

        write_configfile(be_conf_json, be_config_path)

    backend = Backend.query.filter(Backend.id == be_id).first()
    form.set_backend(backend)

    if os.path.isfile(udp_filepath):
        udp_value = read_file(udp_filepath)
    else:
        udp_value = read_file(os.path.join(deliverable_path, "src", "openeo_d28", "body", "EODC_user_process.json"))
    if os.path.isfile(job_filepath):
        job_value = read_file(job_filepath)
    else:
        job_value = read_file(os.path.join(deliverable_path, "src", "openeo_d28", "body", "EODC_job.json"))
    if os.path.isfile(job_sync_filepath):
        job_sync_value = read_file(job_sync_filepath)
    else:
        job_sync_value = read_file(os.path.join(deliverable_path, "src", "openeo_d28", "body", "EODC_job.json"))

    udp_name = "test_udpname"
    pre_job_id = "DEFAULT"
    if os.path.isfile(be_config_path):
        be_conf_json = read_configfile(be_config_path)
        udp_name = be_conf_json["variables"]["process_graph_id"]
        pre_job_id = be_conf_json["variables"]["job_id_precomputed"]

    config_created = os.path.isfile(be_config_path)

    return render_template('backend_deliverable.html', form=form, udp_value=udp_value, config_created=config_created,
                           job_value=job_value, job_sync_value=job_sync_value, udp_name=udp_name, pre_job_id=pre_job_id)


@app.route('/backend/validate/deliverable/<be_id>', methods=['GET', 'POST'])
def backend_validate_deliverable(be_id):
    """
    Validates all endpoints of a backend.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    req = request
    results = run_validation_deliverable(be_id)

    if isinstance(results, str):
        return "<h2>Error during execution! Have you applyed the changes on the D28 validation page?</h2><br>{}".format(str(results))

    backend = Backend.query.filter(Backend.id == be_id).first()

    form = BackendForm(request.form)

    form.set_backend(backend)

    return render_template('backend_validate.html', form=form, results=results)


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

    if backend.output == "result_None.json" or not backend.output:
        backend.output = "result_{}.json".format(backend.id)
        db.session.commit()

    create_configfile(be_id=be_id)

    results = run_validation(be_id)

    return render_template('backend_validate.html', form=form, results=results)


@app.route('/backend/download/<be_id>')
def backend_download(be_id):
    """
    Downloads the configuration of the backend.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    create_configfile(be_id=be_id, plainpwd=False)

    backend = Backend.query.filter(Backend.id == be_id).first()

    if backend.output == "result_None.json":
        backend.output = "result_{}.json".format(backend.id)
        db.session.commit()

    config_path = "config_{}.toml".format(str(be_id))

    config_path = os.getcwd() + "/" + config_path

    return send_file(config_path, as_attachment=True)


@app.route('/backend/validatepytest/<be_id>')
def backend_validate_pytest(be_id):
    """
    Validates all endpoints of a backend with the pytest framework.

    Parameters
    ----------
    be_id : int
        ID of backend
    """
    backend = Backend.query.filter(Backend.id == be_id).first()

    form = BackendForm(request.form)

    form.set_backend(backend)

    if backend.output == "result_None.json":
        backend.output = "result_{}.json".format(backend.id)
        db.session.commit()

    #results = run_validation(be_id)
    result_path = run_pytest_validation(be_id)

    if result_path:
        return redirect(url_for('static', filename=result_path)) # return render_template('backend_validate_pytest.html', form=form, result_path=result_path)


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