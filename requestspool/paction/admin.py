#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/9
Desc    :   
"""
from httpappengine import url, rest
from httpappengine.helper import not_found

from requestspool.util import get_route, get_all_routes


@url("/admin/route/add", "POST")
def route_add(environ, start_response):
    # 尚未实现
    return not_found(start_response)


@url("/admin/route/all", "GET")
def route_show_all(environ, start_response):
    # TODO 尚未完成
    result = {
        "route": []
    }
    for route in get_all_routes():
        r = {}

        result['route'].append(r)
    return rest(start_response, result)


@url("/check", "GET")
def check(environ, start_response):
    # 检测get_route
    get_route('http://test')
    s = "Running!\n"

    start_response("200 OK", [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(s)))
    ])

    return s


@url("/", "GET")
def index(environ, start_response):
    return check(environ, start_response)
