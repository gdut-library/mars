#coding: utf-8

from flask import Flask

from .db import db
from .views import r


def build(**settings):
    app = Flask(__name__)

    app.config.from_envvar('LIB_SERVER_CONFIG', silent=True)
    app.config.update(settings)

    db.init_app(app)
    db.app = app

    app.register_blueprint(r.app, url_prefix='/api')

    return app
