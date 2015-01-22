#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/14
Desc    :   反向代理模块
"""
import urlparse
import urllib
from httpappengine import url

import config
from .http import all_req, show_response


def get_base_url(full_url):
    proto, l = urllib.splittype(full_url)
    host, l = urllib.splithost(l)
    return "%s://%s" % (proto, host)


class RewriteLink(object):
    LOCAL_BASE = "http://localhost:%s/proxy/" % config.PORT

    def __init__(self, base_href):
        self._base_href = base_href

    def __call__(self, link):
        if link.startswith("//"):
            _url = urlparse.urljoin(self.LOCAL_BASE + "http://", link.lstrip('/'))
        elif link.startswith("http://"):
            _url = urlparse.urljoin(self.LOCAL_BASE, link.lstrip('/'))
        else:
            _url = urlparse.urljoin(urlparse.urljoin(self.LOCAL_BASE, self._base_href), link.lstrip('/'))
        return _url


def show_proxy_response(_url, status_code, headers, output, start_response):
    import lxml.html
    if "content-type" in headers and u'text/html' in headers.get("content-type"):
        html = lxml.html.fromstring(output)
        html.rewrite_links(RewriteLink(get_base_url(_url)))
        output = lxml.html.tostring(html)
    return show_response(status_code, headers, output, start_response)

@url("/proxy/http://<path:path_url>", "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS")
def proxy_http_req(path_url, environ, start_response):
    _url = u'http://'+path_url
    status_code, headers, output = all_req(_url, environ, start_response)
    return show_proxy_response(_url, status_code, headers, output, start_response)


@url("/proxy/https://<path:path_url>", "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS")
def proxy_https_req(path_url, environ, start_response):
    _url = u'https://'+path_url
    status_code, headers, output = all_req(_url, environ, start_response)
    return show_proxy_response(_url, status_code, headers, output, start_response)
