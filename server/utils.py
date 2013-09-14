#coding: utf-8

from functools import wraps

from flask import make_response
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

        rv.headers.add('Access-Control-Allow-Origin', '*')
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
