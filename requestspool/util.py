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


def get_route(path_url):
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

    for route in ROUTE_URL:
        if route.match(path_url):
            return route