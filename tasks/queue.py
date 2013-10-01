#coding: utf-8

from redis import Redis
from rq import Queue


__all__ = ['book_queue', 'user_queue']


_redis_connection = Redis()
book_queue = Queue(name='book', connection=_redis_connection)
user_queue = Queue(name='user', connection=_redis_connection)
