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
    import logging
    from logging.handlers import RotatingFileHandler

    log_path = app.config.get('LOG_FILE', 'app.log')
    if app.debug:
        log_path = log_path + '.debug'

    file_handler = RotatingFileHandler(log_path)
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[from %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)

    return app
