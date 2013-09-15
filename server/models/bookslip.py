#coding: utf-8

from server.db import db

from .user import User
from .book import Book


__all__ = ['BookSlip']


books_bookslips = db.Table('books_bookslips',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id')),
    db.Column('bookslip_id', db.Integer, db.ForeignKey('book_slip.id'))
)


class BookSlip(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    books = db.relationship(Book, secondary=books_bookslips,
                            backref=db.backref('book_slip', lazy='select'))
    user = db.relationship(User, backref='book_slip', uselist=False,
                           lazy='select')

    @property
    def __dictify__(self):
        return [i.__dictify__ for i in self.books]
