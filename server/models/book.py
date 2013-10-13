#coding: utf-8

import json
import requests

from server.db import db


__all__ = ['Book', 'BookLocation', 'BookBorrowed']


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ctrlno = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    isbn = db.Column(db.String(20))
    douban_details = db.Column(db.String(5000))  # raw json blob

    location = db.relationship('BookLocation', backref='book', lazy='select',
                               uselist=False)

    @staticmethod
    def get_douban_details(isbn):
        '''根据 isbn 获取豆瓣条目信息

        :param isbn: 书籍 isbn 码
        '''

        if not isbn:
            return
        resp = requests.get('https://api.douban.com/v2/book/isbn/%s' % isbn)
        return resp.ok and resp.text

    def __init__(self, ctrlno, name, isbn, douban_details=None,
                 *args, **kwargs):
        self.ctrlno = ctrlno
        self.name = name
        self.isbn = isbn
        self.douban_details = douban_details or 'null'

    @property
    def __dictify__(self):
        return {
            'ctrlno': self.ctrlno,
            'name': self.name,
            'isbn': self.isbn,
            'douban_details': json.loads(self.douban_details or 'null'),
            'location': self.location.__dictify__
        }


class BookLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(10), nullable=False)
    available = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)

    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))

    @staticmethod
    def from_api(l):
        return {
            'available': len(filter(lambda x: x['status'] == u'可供出借', l)),
            'total': len(l),
            'location': l[0]['location']
        }

    def __init__(self, location, available, total):
        self.location = location
        self.available = available
        self.total = total

    @property
    def __dictify__(self):
        return {
            'location': self.location,
            'available': self.available,
            'total': self.total
        }


class BookBorrowed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    borrowed_date = db.Column(db.DateTime, nullable=False)
    return_deadline = db.Column(db.DateTime, nullable=False)
    renewable = db.Column(db.Integer, default=0)
