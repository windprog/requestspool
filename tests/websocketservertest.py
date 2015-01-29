#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/28
Desc    :   
"""
import os
import geventwebsocket
from geventwebsocket.server import WebSocketServer

PORT = 8000


def echo_app(environ, start_response):
    websocket = environ.get("wsgi.websocket")

    if websocket is None:
        return http_handler(environ, start_response)
    try:
        print "new client"
        while True:
            message = websocket.receive()
            if message is not None:
                print "receive len:%s" % len(message)
            else:
                print "None message"
            websocket.send(message)
        websocket.close()
    except geventwebsocket.WebSocketError, ex:
        print "{0}: {1}".format(ex.__class__.__name__, ex)


def http_handler(environ, start_response):
    if environ["PATH_INFO"].strip("/") == "version":
        start_response("200 OK", [])
        return [agent]

    else:
        start_response("400 Bad Request", [])

        return ["WebSocket connection is expected here."]


path = os.path.dirname(geventwebsocket.__file__)
agent = "gevent-websocket/%s" % (geventwebsocket.get_version())


def visit():
    import websocket
    ws = websocket.create_connection("ws://localhost:%s/" % PORT)
    ws.send(" "*1024*1024*16)
    print ws.recv()

print "try Running %s from %s" % (agent, path)
try:
    WebSocketServer(("", PORT), echo_app, debug=False).serve_forever()
except:
    visit()