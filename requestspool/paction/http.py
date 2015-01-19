#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   wsgi handler
"""
from httpappengine import url
from httplib import responses

from requestspool.util import get_route, get_all_routes
from requestspool.route import TIMEOUT_STATUS_CODE, SERVICE_UNAVAILABLE_STATUS_CODE

# 载入route
get_all_routes()


def all_req(path_url, environ, start_response):
    method = environ.get('REQUEST_METHOD').upper()

    if not (path_url.startswith(u"http://") or path_url.startswith(u"https://")):
        path_url = u"http://" + unicode(path_url)

    req_query_string = environ.get("QUERY_STRING", "")
    try:
        # 获取data
        req_data = environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH', '0')))
    except:
        req_data = None

    requestpool_headers = {}
    req_headers = {}
    for key, val in environ.iteritems():
        if key.startswith('HTTP_'):
            # 生成req_headers 暂无需求
            header_name = key[5:].replace('_', '-')
            if header_name == 'host'.upper():
                continue
            if 'REQUESTSPOOL.' in header_name:
                requestpool_headers[header_name] = val
            else:
                req_headers[header_name] = val

    route = get_route(path_url)
    return route.http_result(requestpool_headers=requestpool_headers,
                             url=path_url, method=method, req_query_string=req_query_string,
                             req_data=req_data, req_headers=req_headers)


def requests_timeout(start_response):
    from httplib import GATEWAY_TIMEOUT
    s = "requests timeout!"

    start_response("{0} {1}".format(GATEWAY_TIMEOUT, responses.get(GATEWAY_TIMEOUT, 'OK')), [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(s)))
    ])

    return (s,)

def requests_service_unavailable(start_response):
    from httplib import SERVICE_UNAVAILABLE
    s = "server overload!"

    start_response("{0} {1}".format(SERVICE_UNAVAILABLE, responses.get(SERVICE_UNAVAILABLE, 'OK')), [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(s)))
    ])

    return (s,)




def show_response(status_code, headers, output, start_response):
    if status_code == TIMEOUT_STATUS_CODE:
        return requests_timeout(start_response)
    elif status_code == SERVICE_UNAVAILABLE_STATUS_CODE:
        return requests_service_unavailable(start_response)
    start_response(
        "{0} {1}".format(status_code, responses.get(status_code, 'OK')),
        headers.items())
    return output

@url("/http://<path:path_url>", "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS")
def http_req(path_url, environ, start_response):
    status_code, headers, output = all_req(u'http://'+path_url, environ, start_response)
    return show_response(status_code, headers, output, start_response)


@url("/https://<path:path_url>", "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS")
def https_req(path_url, environ, start_response):
    status_code, headers, output = all_req(u'https://'+path_url, environ, start_response)
    return show_response(status_code, headers, output, start_response)
