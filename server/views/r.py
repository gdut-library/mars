#coding: utf-8

import time
import logging

from flask import Blueprint, current_app
from flask import request, Response
from flask.views import MethodView

import api
from api import LibraryNetworkError, LibraryNotFoundError

from server.db import db
from server.models import Book, User
from server.helpers import douban_api as douban
from server.helpers.book import store_book_result
from server.helpers.user import (create_user, auth_required,
                                 auth_required_carry_pwd)
from server.utils import (json_view, jsonify, error, LogDuration, ignores,
                          parse_isbn)


app = Blueprint('r', __name__)
logger = logging.getLogger('app')


@app.errorhandler(LibraryNetworkError)
@json_view
def network_error_handler(e):
    '''网络错误处理'''

    logger.error('hitting %s from %s' % (request.url, request.remote_addr))

    return error(u'网络错误', 500)


@app.errorhandler(LibraryNotFoundError)
@json_view
def notfound_error_handler(e):
    '''书籍查找失败处理'''

    logger.warning('hitting %s from %s' % (request.url, request.remote_addr))

    return error(u'书籍没有找到', 404)


@app.route('/user/login', methods=['POST'])
@json_view
@auth_required_carry_pwd
def user_login(username, token, me, password):
    '''用户登录

    假如数据库里没有用户条目，添加到数据库中

    TODO 添加异步任务（查询借阅历史）
    '''
    personal = me.personal(token)
    user = create_user(personal, is_commit=True)

    return jsonify(user=user)


@app.route('/user/me', methods=['GET'])
@json_view
@auth_required
def user_infomations(username, token, me):
    '''获取当前用户信息'''
    user = User.query.filter_by(cardno=username).first()
    if not user:
        personal = me.personal(token)
        user = create_user(personal, check_exists=False, is_commit=True)

    return jsonify(user=user)


class BookSlipView(MethodView):
    decorators = [json_view, auth_required]

    def _get_book_record(self, ctrlno):
        book = Book.query.filter_by(ctrlno=ctrlno).first()

        if not book:
            book_api = api.Book()
            try:
                book_infos = book_api.get(ctrlno)
            except LibraryNotFoundError:
                return False
            book = store_book_result(book_infos, check_exists=False,
                                     is_commit=True)

        return book

    def get(self, username, token, me):
        '''返回用户书单列表'''
        user = User.query.filter_by(cardno=username).first()

        return jsonify(books=user.book_slip)

    def put(self, username, token, me, ctrlno):
        '''往用户书单里添加一本图书

        如果添加的书籍不存在，返回 404

        :param ctrlno: 书籍编号
        '''
        user = User.query.filter_by(cardno=username).first()
        book = self._get_book_record(ctrlno)

        if not book:
            return jsonify(msg=u'添加的书籍不存在'), 404

        user.book_slip.books.append(book)
        db.session.commit()

        return jsonify(books=user.book_slip), 201

    def delete(self, username, token, me, ctrlno):
        '''从用户书单里移除书籍

        如果需要移除的书籍不在书单里，返回 404

        :param ctrlno: 书籍编号，如果值为 `all` 则清空整个书单
        '''
        user = User.query.filter_by(cardno=username).first()
        book_slip = user.book_slip

        if ctrlno == u'all':
            book_slip.books = book_slip.books[0:0]
        else:
            book = self._get_book_record(ctrlno)

            if not book or book not in book_slip.books:
                return jsonify(msg=u'需要移除的书籍不存在'), 404

            book_slip.books.remove(book)

        db.session.commit()
        return Response(status=204)


book_slip_view = BookSlipView.as_view('bookslip')
app.add_url_rule('/user/books/<string:ctrlno>', view_func=book_slip_view,
                 methods=['PUT', 'DELETE'])
app.add_url_rule('/user/books', view_func=book_slip_view,
                 methods=['GET'])


@app.route('/book/<string:ctrlno>', methods=['GET'])
@json_view
def book(ctrlno):
    '''根据 ctrlno 获取书籍信息

    TODO 将更新库存单独出来
    TODO 添加调用次数限制
    '''
    book = Book.query.filter_by(ctrlno=ctrlno).first()
    if not book:
        try:
            book_api = api.Book()
            book_infos = book_api.get(ctrlno)
        except LibraryNotFoundError:
            return error(u'没有找到图书 %s' % ctrlno, 404)

        book = store_book_result(book_infos, True)

    return jsonify(book=book)


@app.route('/book/search', methods=['GET'])
@json_view
@LogDuration(logger.debug, 'search start', 'search end %d')
def book_search():
    '''根据任意关键字查询书籍

    :param q: 关键字
    :param limit: 结果限制，默认为 10, 最多为 30
    :param verbose: 是否包含书籍详细信息

    TODO 添加调用次数限制
    '''

    q = request.args.get('q')
    if not q:
        return jsonify(error=u'请指定查询关键字'), 403

    verbose = int(request.args.get('verbose', 0))
    limit = min(int(request.args.get('limit', 10)), 30)
    verbose = True if verbose else False

    # ISBN 查询
    with ignores(ValueError):
        isbns = parse_isbn(str(int(q.replace('-', '')))).values()

        # 先查询本地
        for isbn in isbns:
            book = Book.query.filter_by(isbn=isbn).first()
            if book:
                return jsonify(books=[book])

        # 查询服务器端
        book_api = api.Book()
        for isbn in isbns:
            with ignores(LibraryNotFoundError):
                books = book_api.search(isbn, verbose=True)

                for book in books:
                    store_book_result(book['details'], check_exists=False)
                db.session.commit()

                return jsonify(books=books)

        raise LibraryNotFoundError

    # 调用 douban api 查询
    results, start = [], time.time()
    timeout = current_app.config.get('SEARCH_TIMEOUT', 10)
    for raw in douban.search(q, limit=200):  # 有些书可能图书馆没有
        if time.time() - start > timeout:  # 超时
            break
        if len(results) >= limit:
            break
        book = douban.book_mocking(raw)
        if book:
            results.append(book)
    db.session.commit()  # 保存新增的记录

    if not results:
        raise LibraryNotFoundError

    return jsonify(books=results)
