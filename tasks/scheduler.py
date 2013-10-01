#coding: utf-8

from redis import Redis
from rq_scheduler import Scheduler


__all__ = ['scheduler']


_redis_connection = Redis()
scheduler = Scheduler(connection=_redis_connection)
