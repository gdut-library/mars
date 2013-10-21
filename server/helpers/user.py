#coding: utf-8

from functools import wraps
from flask import request

import api
from api import LibraryChangePasswordError, LibraryLoginError

from server.utils import error
from server.db import db
from server.models import User, BookSlip


__all__ = ['create_user', 'AuthRequired', 'auth_required',
           'auth_required_carry_pwd']


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
