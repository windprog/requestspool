#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/19
Desc    :   
"""
from requestspool.update import BackendRun
from gevent import monkey
import gevent
import time
monkey.patch_all()

from route_default import route

s = route[0]._speed

def f1():
    time.sleep(3)
    t = s._callback
    assert isinstance(t, BackendRun)
    t.add(route=route[0], method="GET", url="http://www.baidu.com", req_query_string="", req_headers="", req_data="")
    t.add(route=route[0], method="GET", url="http://www.baidu.com/test", req_query_string="", req_headers="", req_data="")
    t.add(route=route[0], method="GET", url="http://www.baidu.com/test1", req_query_string="", req_headers="", req_data="")


gevent.joinall([
    s._spawn,
    gevent.spawn(f1)
], timeout=34)
