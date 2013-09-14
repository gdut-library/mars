#coding: utf-8

from flask.ext.script import Manager

from server import app as server_app
from server.db import db


app = server_app.build()
manager = Manager(app)


@manager.command
def run():
    app.run(host='0.0.0.0', port=9001, debug=True)


@manager.command
def init_db():
    from server import models
    db.create_all()


if __name__ == '__main__':
    manager.run()
