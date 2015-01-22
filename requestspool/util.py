#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/6
Desc    :   方法集合
"""
from importlib import import_module


def get_all_routes():
    if 'ROUTE_URL' not in globals():
        from interface import BaseRoute
        from . import config

        # 从route模块中选择route对象
        for name, val in vars(import_module(config.ROUTE_MOD)).iteritems():
            if isinstance(val, list) and isinstance(val[0], BaseRoute):
                ROUTE_URL = val
                break
        else:
            raise ImportError(u'没有找到路由列表,请参考route_default.py')
        globals()['ROUTE_URL'] = ROUTE_URL
    else:
        ROUTE_URL = globals()['ROUTE_URL']
    return ROUTE_URL


def get_route(path_url):
    ROUTE_URL = get_all_routes()
    for route in ROUTE_URL:
        if route.match(path_url):
            return route


def backend_call(callback, **kwargs):
    import gevent
    import config
    if not config.DEBUG:
        return gevent.spawn(callback, **kwargs)
    else:
        import threading

        t = threading.Thread(target=callback, kwargs=kwargs)
        t.start()
        return t


def patch_requests():
    '''
        gevent patch
        test it work in requests==2.5.1
    '''
    import gevent.socket
    import httplib
    setattr(httplib, "socket", gevent.socket)
    import requests.packages.urllib3.connection
    setattr(requests.packages.urllib3.connection, "socket", gevent.socket)
    import requests.packages.urllib3.connectionpool
    setattr(requests.packages.urllib3.connectionpool, "socket", gevent.socket)
    import requests.packages.urllib3.util.connection
    setattr(requests.packages.urllib3.util.connection, "socket", gevent.socket)
    # 这个是自行编写的
    import requests.utils
    setattr(requests.utils, "socket", gevent.socket)


def pdb_pm():
    from sys import exc_info
    from traceback import print_exc
    from pdb import post_mortem
    # 使用 pdb 进入异常现场。
    _, _, tb = exc_info()
    print_exc()
    # 进入PDB
    post_mortem(tb)
