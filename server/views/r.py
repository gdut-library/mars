#coding: utf-8

from functools import wraps

from flask import Blueprint
from flask import request

import api
from api import (
    LibraryChangePasswordError, LibraryLoginError,
    LibraryNotFoundError
)

from server.utils import json_view, jsonify
from server.db import db
from server.models import User, Book, BookLocation

app = Blueprint('r', __name__)


def auth_required(func):
    @wraps(func)
    def check_auth(*args, **kwargs):
        me = api.Me()
        token = request.headers['X-LIBRARY-TOKEN']

        if not me.check_login(token):
            return jsonify(error=u'登录过期'), 401

        return func(token, me, *args, **kwargs)

    return check_auth


def store_book_result(book_infos, is_commit=False):
    '''保存书籍查询信息

    :param book_infos: 书籍查询结果
    :param is_commit: 是否在执行完后执行 commit
    '''
    book = Book.query.filter_by(ctrlno=book_infos['ctrlno']).first()
    if book:
        return book

    locations = book_infos.pop('locations')

    book = Book(**book_infos)
    db.session.add(book)

    available = len(filter(lambda x: x['status'] == u'可供出借',
                           locations))
    total = len(locations)
    location = BookLocation(locations[0]['location'], available, total)
    location.book = book
    db.session.add(location)

    if is_commit:
        db.session.commit()

    return book


@app.route('/user/login', methods=['POST'])
@json_view
def user_login():
    me = api.Me()
    username = request.form['username']
    password = request.form['password']

    try:
        token = me.login(username, password).values()[0]
    except LibraryChangePasswordError, e:
        return jsonify(error=u'需要激活账户', next=e.next), 403
    except LibraryLoginError:
        return jsonify(error=u'登录失败'), 403

    personal = me.personal(token)
    user = User.query.filter_by(cardno=personal['cardno']).first()
    if not user:
        user = User(**personal)
        db.session.add(user)
        db.session.commit()

    return jsonify(token=token, user=user)


@app.route('/user/me', methods=['GET'])
@json_view
@auth_required
def user_infomations(token, me):
    # TODO
    # 应该能从数据库里获取而不是要查询图书馆
    personal = me.personal(token)

    return jsonify(user=personal)


@app.route('/book/<string:ctrlno>', methods=['GET'])
@json_view
def book(ctrlno):
    # TODO
    # 添加调用次数限制

    book = Book.query.filter_by(ctrlno=ctrlno).first()
    if not book:
        try:
            book_api = api.Book()
            book_infos = book_api.get(ctrlno)
        except LibraryNotFoundError:
            return jsonify(error=u'没有找到图书 %s' % ctrlno), 404

        book = store_book_result(book_infos, True)

    return jsonify(book=book)


@app.route('/book/search', methods=['GET'])
@json_view
def book_search():
    # TODO
    # 添加调用次数限制

    q = request.args.get('q')
    verbose = int(request.args.get('verbose', 0))
    limit = int(request.args.get('limit', 0))
    verbose = True if verbose else False

    book = api.Book()
    results = book.search(q, verbose, limit)

    return jsonify(books=results)
