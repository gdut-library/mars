#coding: utf-8

import os

DEBUG = True

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath('data/server.db')

SECRET_KEY = 'gdut library rocks'

LOGGING_CONFIG = {
    'formatters': {
        'brief': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        }
    },
    'filters': [],
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'brief'
        },
        'logfile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.abspath('logs/app.debug.log'),
            'formatter': 'brief'
        }
    },
    'loggers': {
        'app': {
            'propagate': True,
            'level': 'DEBUG',
            'handlers': ['console', 'logfile']
        },
        'tasks': {
            'propagate': False,
            'level': 'DEBUG',
            'handlers': ['logfile', 'console']
        }
    },
    'disable_existing_loggers': True,
    'incremental': False,
    'version': 1
}
