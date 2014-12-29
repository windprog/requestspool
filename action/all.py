#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   
"""
from httpappengine.decorator import url
from httpappengine.helper import not_found
from config import ROUTE_URL
from requestspool.http import call_http_request
import urlparse
from httplib import responses
from wsgiref.util import is_hop_by_hop


def all_req(path_url, environ, start_response):
    method = environ.get('REQUEST_METHOD').upper()

    if not (path_url.startswith(u"http://") or path_url.startswith(u"https://")):
        path_url = u"http://" + unicode(path_url)

    query_dict = urlparse.parse_qs(environ.get("QUERY_STRING", ""))
    try:
        # 获取data
        data = environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH', '0')))
    except:
        data = None

    result = None
    for route in ROUTE_URL:
        if route.match(path_url):
            result = route.call_http_request(url=path_url, method=method, params=query_dict, data=data)
            break

    if result:
        headers = result.headers
        for key, val in headers.iteritems():
            if is_hop_by_hop(key):
                headers.pop(key)
            elif key.lower() == 'content-encoding' and 'zip' in val:
                headers.pop(key)
        status_code = result.status_code
        text = result.text
        Content_Type = headers.get('Content-Type')
        Content_Type_list = Content_Type.split(';')
        if len(Content_Type_list) >= 2:
            Content_Type_list[1] = ' charset=utf-8'
        headers['Content-Type'.lower()] = str(';'.join(Content_Type_list))
        output = text.encode('utf-8')
        headers['Content-Length'.lower()] = str(len(output))
        start_response("{0} {1}".format(status_code, responses.get(status_code, 'OK')), headers.items())
        return output
    else:
        return not_found(start_response)

@url("/http://<path:path_url>", "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS")
def http_req(path_url, environ, start_response):
    return all_req(u'http://'+path_url, environ, start_response)


@url("/https://<path:path_url>", "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS")
def https_req(path_url, environ, start_response):
    return all_req(u'https://'+path_url, environ, start_response)


@url("/admin/route/add", "POST")
def route_add(environ, start_response):
    # 尚未实现
    return not_found(start_response)

@url("/admin/route/all", "GET")
def route_add(environ, start_response):
    # 尚未实现
    return not_found(start_response)