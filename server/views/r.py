#coding: utf-8

import time
import logging
from functools import wraps

from flask import Blueprint
from flask import request, Response
from flask.views import MethodView

import api
from api import (
    LibraryChangePasswordError, LibraryLoginError,
    LibraryNotFoundError, LibraryNetworkError
)

from server.utils import json_view, jsonify, error
from server.db import db
from server.models import User, Book, BookLocation, BookSlip

app = Blueprint('r', __name__)
logger = logging.getLogger('app')


class AuthRequired(object):
    '''对调用请求进行用户登录验证的装饰器，
    被装饰函数在调用时会填入 `username`, `token` 和 `api.me` 实例，
    假如 `pass_pwd` 为真，将填入用户密码 `password`

    如果登录失败，返回 `登录失败`, 403
    如果需要激活，返回 `需要激活帐号`, 403 以及验证地址

    :param pass_pwd: 是否填入用户密码, 默认为否
    '''
    def __init__(self, pass_pwd=None):
        self.pass_pwd = pass_pwd or pass_pwd

    def __call__(self, func):
        @wraps(func)
        def check_auth(*args, **kwargs):
            me = api.Me()
            username = request.headers.get('X-LIBRARY-USERNAME')
            password = request.headers.get('X-LIBRARY-PASSWORD')

            try:
                cookies = me.login(username, password)
            except LibraryChangePasswordError, e:
                return error(u'需要激活帐号', next=e.next,
                             status_code=403)
            except LibraryLoginError, e:
                return error(u'登录失败', 403)

            token = cookies.values()[0]

            if self.pass_pwd:
                return func(username, token, me, password, *args, **kwargs)
            else:
                return func(username, token, me, *args, **kwargs)

        return check_auth

auth_required = AuthRequired()
auth_required_carry_pwd = AuthRequired(True)


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


def create_user(user_infos, check_exists=True, is_commit=False):
    '''创建用户

    :param user_infos: 用户信息
    :param check_exists: 是否先检查数据库里面是否存在
    :param is_commit: 是否在执行完后执行 commit
    '''

    if check_exists:
        user = User.query.filter_by(cardno=user_infos['cardno']).first()
        if user:
            return user

    user = User(**user_infos)
    user.book_slip = BookSlip()
    db.session.add(user.book_slip)
    db.session.add(user)

    if is_commit:
        db.session.commit()

    return user


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
def book_search():
    '''根据任意关键字查询书籍

    :param q: 关键字
    :param limit: 结果限制，默认为 20
    :param verbose: 是否包含书籍详细信息

    TODO 添加调用次数限制
    '''

    q = request.args.get('q')
    verbose = int(request.args.get('verbose', 0))
    limit = int(request.args.get('limit', 20))
    verbose = True if verbose else False

    if not q:
        return jsonify(error=u'请指定查询关键字'), 403

    logger.debug('search duration start')
    started = time.time()
    book = api.Book()
    results = book.search(q, verbose, limit)
    logger.debug('search duration end: %d', int(time.time() - started))

    return jsonify(books=results)
