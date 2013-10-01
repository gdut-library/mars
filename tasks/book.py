#coding: utf-8

from flask import current_app

import api
from api import LibraryNotFoundError

from server.app import build
from server.db import db
from server.models import Book

from .queue import book_queue


__all__ = ['update_book', 'update_books']


def update_book(ctrlno):
    '''更新书籍信息

    :param ctrlno: 书籍控制号
    :param database: 数据库

    TODO isolate location updating
    '''
    try:
        book_api = api.Book()
        book_infos = book_api.get(ctrlno)
    except LibraryNotFoundError:
        return

    app = build()
    with app.app_context():
        book = Book.query.filter_by(ctrlno=ctrlno).first()
        if not book:
            return

        locations = book_infos.get('locations')
        book.location.available = len(
            filter(lambda x: x['status'] == u'可供出借', locations))
        book.location.total = len(locations)
        db.session.commit()

    return book_infos


def update_books():
    '''更新所有书籍信息'''

    app = build()
    with app.app_context():
        current_app.logger.debug('start updating all books...')
        for book in Book.query.all():
            book_queue.enqueue(update_book, book.ctrlno)

    return True
