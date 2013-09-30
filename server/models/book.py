#coding: utf-8

from server.db import db


__all__ = ['Book', 'BookLocation', 'BookBorrowed']


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ctrlno = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    isbn = db.Column(db.String(20))

    location = db.relationship('BookLocation', backref='book', lazy='select',
                               uselist=False)

    def __init__(self, ctrlno, name, isbn, *args, **kwargs):
        self.ctrlno = ctrlno
        self.name = name
        self.isbn = isbn

    @property
    def __dictify__(self):
        return {
            'ctrlno': self.ctrlno,
            'name': self.name,
            'isbn': self.isbn,
            'location': self.location.__dictify__
        }


class BookLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(10), nullable=False)
    available = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)

    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))

    def __init__(self, location, available, total):
        self.location = location
        self.available = available
        self.total = total

    def update(self, location, available, total):
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
