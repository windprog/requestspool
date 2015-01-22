#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/21
Desc    :   
"""
import gevent
from gevent.monkey import patch_all, patch_socket
import time

patch_all()

HOST = 'localhost'
# 端口
PORT = 17117
# 存放缓存的数据库名称
DB_NAME = 'http_cache'
# 用户名
USER = 'test'
# 密码
PW = 'test'
# 存放 gridfs 的 mongodb collection 名称
COLL_NAME = 'test'


def get_db_con():
    from pymongo import MongoClient
    con = MongoClient(HOST, PORT, use_greenlets=True)
    db = con[COLL_NAME]
    try:
        db.authenticate(USER, PW)
    except:
        pass

    def init():
        db[COLL_NAME].save({
            "_id":"test",
            "name": "test",
        })
    init()
    return db, con
# --------------------------------------------------

from gevent.threadpool import ThreadPool
from gevent.event import Event
pool = ThreadPool(1)


def worker1():
    gevent.sleep(3)


class Counter(object):
    count = 0


e = Event()


def worker2():
    time.sleep(5)
    db, con = get_db_con()
    print "start"
    e.set()
    for _ in xrange(1):
        Counter.count += 1
        assert "name" in db[COLL_NAME].find_one({"_id":"test"})


def worker3():
    e.wait()
    db, con = get_db_con()
    for _ in xrange(1):
        Counter.count += 1
        assert "name" in db[COLL_NAME].find_one({"_id":"test"})


jobs = [
    pool.spawn(worker1)
]
for _ in xrange(1):
    jobs.append(pool.spawn(worker2))
    jobs.append(pool.spawn(worker3))
d1 = time.time()
pool.join()
d2 = time.time()
print d2-d1
print Counter.count
