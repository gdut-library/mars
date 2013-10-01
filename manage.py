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


@manager.command
def update_books():
    from tasks import scheduler, update_books
    from datetime import datetime

    scheduler.schedule(datetime.now(), update_books, interval=24 * 60 * 60)


if __name__ == '__main__':
    manager.run()
