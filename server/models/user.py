#coding: utf-8

from server.db import db


__all__ = ['User']


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cardno = db.Column(db.String(12), unique=True)
    name = db.Column(db.String(30))
    faculty = db.Column(db.String(30))
    major = db.Column(db.String(30))

    book_slip_id = db.Column(db.Integer, db.ForeignKey('book_slip.id'))
    borrowed_history = db.relationship('BookBorrowed', backref='user',
                                       lazy='select')

    def __init__(self, cardno, name, faculty, major, *args, **kwargs):
        self.cardno = cardno
        self.name = name
        self.faculty = faculty
        self.major = major

    @property
    def __dictify__(self):
        return {
            'cardno': self.cardno,
            'name': self.name,
            'faculty': self.faculty,
            'major': self.major
        }
