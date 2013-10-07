#coding: utf-8

from flask import Flask

from .db import db


def build(**settings):
    app = Flask(__name__)

    app.config.from_envvar('LIB_SERVER_CONFIG', silent=True)
    app.config.update(settings)

    db.init_app(app)
    db.app = app

    register_blueprint(app)
    register_logging(app)

    return app


def register_blueprint(app):
    from .views import r
    app.register_blueprint(r.app, url_prefix='/api')

    return app


def register_logging(app):
    import logging.config

    logging.config.dictConfig(app.config['LOGGING_CONFIG'])

    return app
