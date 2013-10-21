#coding: utf-8

from server.db import db
from server.models import Book, BookLocation


__all__ = ['store_book_result']


def store_book_result(book_infos, check_exists=True, is_commit=False):
    '''保存书籍查询信息

    :param book_infos: 书籍查询结果
    :param check_exists: 是否先检查数据库里面是否存在
    :param is_commit: 是否在执行完后执行 commit
    '''

    if check_exists:
        book = Book.query.filter_by(ctrlno=book_infos['ctrlno']).first()
        if book:
            return book

    locations = book_infos.pop('locations')

    book = Book(**book_infos)
    db.session.add(book)

    location = BookLocation(**BookLocation.from_api(locations))
    location.book = book
    db.session.add(location)

    if is_commit:
        db.session.commit()

    return book
