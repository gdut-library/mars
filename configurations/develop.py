#coding: utf-8

import os

DEBUG = True

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath('data/server.db')

SECRET_KEY = 'gdut library rocks'

LOG_FILE = os.path.abspath('logs/app.log')

EMAIL_ENABLE = True
EMAIL_LOGIN = None
EMAIL_PWD = None
EMAIL_DEST = []
