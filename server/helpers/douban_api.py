#coding: utf-8

import logging
import requests

import api

from server.models import Book
from server.utils import parse_isbn, ignores, LogDuration
from .book import store_book_result


__all__ = ['search', 'book_mocking']
logger = logging.getLogger('app')
BASIC_URL = 'https://api.douban.com/v2/book/'


def _build_url(scope):
    return BASIC_URL + scope


@LogDuration(logger.debug, 'start book mocking', 'finish book mocking %d')
def book_mocking(db_book):
    '''将豆瓣方面返回的图书信息处理成 api 调用的形式'''
    isbn = parse_isbn(db_book.get('isbn10', ''))

    # 检查数据库里是否有记录
    for i in isbn.values():
        book = Book.query.filter_by(isbn=i).first()
        if book:
            return book

    # 查询图书馆端
    book_api = api.Book()
    book = None
    with ignores(api.LibraryNotFoundError):
        for i in [isbn['isbn10-hyphen'], isbn['isbn13-hyphen']]:
            results = book_api.search(i)
            if results:
                book_infos = book_api.get(results[0]['ctrlno'])
                book = store_book_result(book_infos, check_exists=True)
                return book

    return None


def search(q, limit=20):
    '''查询豆瓣'''
    url = _build_url('search')
    params = {'q': q, 'count': limit}
    resp = requests.get(url, params=params)

    if resp.ok:
        return resp.json().get('books', [])
