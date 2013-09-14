#coding: utf-8

from werkzeug.contrib.fixers import ProxyFix

from server import app as server_app

app = server_app.build()

app.wsgi_app = ProxyFix(app.wsgi_app)


if __name__ == '__main__':
    app.run()
