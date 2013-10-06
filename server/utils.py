#coding: utf-8

from functools import wraps

from flask import make_response, request
from flask import jsonify as _jsonify

from server.db import db


def json_view(func):
    @wraps(func)
    def allow_CORS(*args, **kwargs):
        resp = func(*args, **kwargs)

        #: Handle the different cases of
        #: http://flask.pocoo.org/docs/quickstart/#about-responses
        rv = None
        status = None
        headers = None
        if isinstance(resp, tuple):
            if len(resp) == 3:
                rv, status, headers = resp
            else:
                rv, status = resp
        else:
            rv = resp
        if isinstance(rv, str) or isinstance(rv, unicode):
            rv = make_response(rv)

        origin = request.headers.get('Origin', None)
        if origin:
            rv.headers.add('Access-Control-Allow-Origin', origin)
        return rv, status, headers
    return allow_CORS


def jsonify(**kwargs):
    for k, v in kwargs.items():
        if isinstance(v, db.Model):
            try:
                kwargs[k] = v.__dictify__
            except AttributeError:
                pass
    return _jsonify(**kwargs)


def error(msg, status_code=500, *args, **kwargs):
    return jsonify(error=msg, *args, **kwargs), status_code


# TODO
# - add topic
# - async sending
def send_mail(app, msg):
    if not app.config.get('EMAIL_ENABLE', False) or app.debug:
        return

    import smtplib

    username = app.config.get('EMAIL_LOGIN')
    password = app.config.get('EMAIL_PWD')
    dest = app.config.get('EMAIL_DEST')

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(username, dest, msg)
    server.quit()
