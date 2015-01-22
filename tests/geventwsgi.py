#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/20
Desc    :   
"""
from requestspool.paction.http import application
from requestspool.config import HOST, PORT
from gevent.monkey import patch_all

from gevent import pywsgi

from socket import AF_INET, SOL_SOCKET, SO_REUSEADDR
from gevent.socket import socket

import gevent

_listen_sock = socket(family=AF_INET)
_listen_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
_listen_sock.bind((HOST, PORT))
_listen_sock.listen(2048)
_listen_sock.setblocking(0)

patch_all()

import StringIO
debugs = StringIO.StringIO()


def prof_call(func, *args):
    from cProfile import Profile
    from pstats import Stats
    from httpappengine.engine.config import settings
    # 输出函数调用性能分析。
    prof = Profile(builtins=False)
    ret = prof.runcall(func, *args)

    Stats(prof).sort_stats("cumtime").print_stats(settings.PROJECT_PATH)
    return ret


def yappi_prof_call(func, *args):
    import yappi
    yappi.start()
    result = func(*args)
    yappi.get_func_stats().print_all()
    yappi.get_thread_stats().print_all()
    return result


def gevent_profiler__prof_call(func, *args):
    import gevent_profiler
    return gevent_profiler.profile(func, *args)


def app(environ, start_response):
    # 使用性能统计
    return prof_call(application, environ, start_response)



if __name__ == '__main__':
    print('Serving on %s...' % PORT)
    s = pywsgi.WSGIServer(_listen_sock, application, log=None)
    event = s._stop_event

    def stop():
        gevent.sleep(10)
        event.set()
    # 获取 定时10秒 整体服务器性能统计
    # gevent.spawn(stop)
    # yappi_prof_call(s.serve_forever)
    s.serve_forever()
