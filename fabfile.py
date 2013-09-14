#coding: utf-8

from fabric.api import *

env.use_ssh_config = True


def sync_server_config():
    with cd('/home/hbc/workshop/gdut-library-server'):
        put('supervisord.conf', 'supervisord.conf')
        put('server.nginx.conf', 'server.nginx.conf')
        put('configurations/production.py', 'config/production.py')


def deploy():
    sync_server_config()
