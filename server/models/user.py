#coding: utf-8

from server.db import db


__all__ = ['User']


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cardno = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(30))
    faculty = db.Column(db.String(30))
    major = db.Column(db.String(30))

    book_slip_id = db.Column(db.Integer, db.ForeignKey('book_slip.id'))
    borrowed_history = db.relationship('BookBorrowed', backref='user',
                                       lazy='select')
