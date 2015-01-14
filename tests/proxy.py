#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/14
Desc    :   
"""
from wsgiref.util import is_hop_by_hop
from collections import OrderedDict
from gevent import monkey
import requests
from httplib import responses
import lxml.html
import urlparse
import urllib

monkey.patch_all()

PORT = 8000


def call_http_request(url, method, req_headers=None, req_data=None, req_query_string=None, **kwargs):
    return getattr(requests, method.lower())('%s' % url, params=req_query_string, data=req_data, headers=req_headers, **kwargs)


def sort_headers(headers):
    # 根据headers name 进行排序
    assert hasattr(headers, "__iter__")
    return OrderedDict(sorted(headers.iteritems(), key=lambda d: d[0]))


def parse_requests_result(result):
    headers = result.headers
    for key, val in headers.iteritems():
        if is_hop_by_hop(key):
            headers.pop(key)
        elif key.lower() == 'content-encoding' and 'zip' in val:
            headers.pop(key)
    status_code = result.status_code
    output = result.content
    # 重新排序header，保持与缓存返回的一致性
    headers = sort_headers(headers)
    return status_code, headers, output


def get_http_result(**kwargs):
    return parse_requests_result(call_http_request(**kwargs))


class RewriteLink(object):
    LOCAL_BASE = "http://localhost:%s/" % PORT

    def __init__(self, base_href):
        self._base_href = base_href

    def __call__(self, link):
        if not link.startswith("//"):
            url = urlparse.urljoin(urlparse.urljoin(self.LOCAL_BASE, self._base_href), link.lstrip('/'))
        else:
            url = urlparse.urljoin(self.LOCAL_BASE, link.lstrip('/'))
        return url

LAST_REQ_BASE_URL = "LAST_REQ_BASE_URL"


def get_base_url(full_url):
    proto, l = urllib.splittype(full_url)
    host, l = urllib.splithost(l)
    return "%s://%s" % (proto, host)

def all_req(environ, start_response):
    path_url = environ['PATH_INFO']
    assert path_url.startswith("/")
    path_url = path_url[1:]
    method = environ.get('REQUEST_METHOD').upper()

    if not (path_url.startswith(u"http://") or path_url.startswith(u"https://")):
        path_url = u"http://" + unicode(path_url)
    if path_url != u'http://favicon.ico':
        setattr(all_req, LAST_REQ_BASE_URL, get_base_url(path_url))
    else:
        path_url = getattr(all_req, LAST_REQ_BASE_URL, "") + "/favicon.ico"

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
            # 禁用缓存
            if "CACHE-CONTROL" in header_name:
                continue
            elif "IF-MODIFIED-SINCE" in header_name:
                continue
            # 禁用复用
            if "CONNECTION" in header_name:
                continue
            if "CACHE-CONTROL" in header_name:
                continue
            if 'REQUESTSPOOL.' in header_name:
                requestpool_headers[header_name] = val
            else:
                req_headers[header_name] = val

    status_code, headers, output = get_http_result(url=path_url, method=method, req_query_string=req_query_string,
                                                   req_data=req_data, req_headers=req_headers)

    if "content-type" in headers and u'text/html' in headers.get("content-type"):
        html = lxml.html.fromstring(output)

        html.rewrite_links(RewriteLink(get_base_url(path_url)))
        output = lxml.html.tostring(html)

    start_response(
        "{0} {1}".format(status_code, responses.get(status_code, 'OK')),
        headers.items())
    return (output,)


def debug(environ, start_response):
    from sys import exc_info
    from traceback import print_exc
    from pdb import post_mortem
    try:
        return all_req(environ, start_response)
    except:
        _, _, tb = exc_info()
        print_exc()
        post_mortem(tb)

if __name__ == '__main__':
    print 'Serving on %s...' % PORT

    from gevent.pywsgi import WSGIServer
    WSGIServer(('0.0.0.0', PORT), all_req).serve_forever()
