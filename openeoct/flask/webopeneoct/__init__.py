from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(basedir, 'openeoct.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB maximum upload file size
app.config['BODY_PATH'] = "body"
app.config['D28_Folder'] = "/data/REPO/openeo-D28"
db = SQLAlchemy(app)

from openeoct.flask.webopeneoct import views, models

# needs to be executed in the first time, to create the sqlite database
db.create_all()
