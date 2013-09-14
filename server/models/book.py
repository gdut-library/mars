#coding: utf-8

from server.db import db


__all__ = ['Book', 'BookLocation', 'BookBorrowed']


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ctrlno = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    isbn = db.Column(db.String(20), nullable=False)

    locations = db.relationship('BookLocation', backref='book', lazy='select')


class BookLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    library = db.Column(db.String(10))
    location = db.Column(db.String(10), nullable=False)
    available = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)

    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))


class BookBorrowed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    borrowed_date = db.Column(db.DateTime, nullable=False)
    return_deadline = db.Column(db.DateTime, nullable=False)
    renewable = db.Column(db.Integer, default=0)
