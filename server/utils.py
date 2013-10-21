#coding: utf-8

import time
from functools import wraps
from contextlib import contextmanager
from logging.handlers import SMTPHandler as _SMTPHandler

from flask import make_response, request
from flask import jsonify as _jsonify

import pyisbn
from isbn_hyphenate import isbn_hyphenate

from server.db import db


@contextmanager
def ignores(*exceptions):
    try:
        yield
    except exceptions:
        pass


class SMTPHandler(_SMTPHandler):
    '''SMTP logging handler adapter'''

    def __init__(self, *args, **kwargs):
        super(SMTPHandler, self).__init__(*args, **kwargs)
        self._timeout = 15  # give me more time!


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
    def dictify(model):
        return model.__dictify__

    for k, v in kwargs.items():
        with ignores(AttributeError):
            if isinstance(v, db.Model):
                kwargs[k] = dictify(v)
            elif isinstance(v, list):
                kwargs[k] = [dictify(i) for i in v]

    return _jsonify(**kwargs)


def error(msg, status_code=500, *args, **kwargs):
    return jsonify(error=msg, *args, **kwargs), status_code


class LogDuration(object):

    def __init__(self, log, start, end, log_duration=True):
        self.log = log
        self.start = start or ''
        self.end = end or ''
        self.log_duration = log_duration

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            self.log(self.start)

            resp = func(*args, **kwargs)

            if self.log_duration:
                self.log(self.end % (time.time() - start))
            else:
                self.log(self.end)
            return resp
        return wrapper


def parse_isbn(raw):
    '''将 isbn 转换成 10 / 13 位以及带 hyphen 形式'''

    a, b = raw, raw
    isbn = {
        'isbn10': raw,
        'isbn13': raw,
        'isbn10-hyphen': raw,
        'isbn13-hyphen': raw
    }

    with ignores(pyisbn.IsbnError):
        a = pyisbn.convert(raw)
        b = pyisbn.convert(a)
        isbn = {'isbn%d' % len(i): i for i in [a, b]}

    with ignores(isbn_hyphenate.IsbnMalformedError):
        isbn['isbn10-hyphen'] = isbn_hyphenate.hyphenate(isbn['isbn10'])
        isbn['isbn13-hyphen'] = isbn_hyphenate.hyphenate(isbn['isbn13'])

    return isbn
