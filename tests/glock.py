#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/18
Desc    :   
"""
from gevent import sleep
import gevent
from gevent.lock import BoundedSemaphore

sem = BoundedSemaphore(3)

def worker1():
    with sem:
        gevent.sleep(3)
        print "finish one"

def worker2():
    with sem:
        gevent.sleep(3)
        print "finish two"

jobs = []
for i in range(10):
    jobs.append(gevent.spawn(worker1))
    jobs.append(gevent.spawn(worker2))

gevent.joinall(jobs)
