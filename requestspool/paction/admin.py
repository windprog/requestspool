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
import json
import re
import gevent

from requestspool.util import gen_user_id
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


@url("/publish", methods=None)
def publish(environ, start_response):
    if "wsgi.websocket" in environ:
        import geventwebsocket
        from requestspool.publish import ClientService

        websocket = environ.get("wsgi.websocket")
        try:
            _config = json.loads(websocket.receive())
            new_user_id = gen_user_id()
            while True:
                if new_user_id in ClientService.clients:
                    new_user_id = gen_user_id()
                else:
                    break

            client = ClientService(websocket, new_user_id, _config)
            while True:
                client.one_send()
                gevent.sleep(0)
        except geventwebsocket.WebSocketError, ex:
            print "{0}: {1}".format(ex.__class__.__name__, ex)
        finally:
            try:
                websocket.close()
                client.close()
            except:
                pass
    else:
        return check(environ, start_response)
