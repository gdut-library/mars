#coding: utf-8

from flask import Flask

from .db import db


def build(**settings):
    app = Flask(__name__)

    app.config.from_envvar('LIB_SERVER_CONFIG', silent=True)
    app.config.update(settings)

    db.init_app(app)
    db.app = app

    return app
