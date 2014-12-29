#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   
"""
import urllib
import requests
import urlparse


def call_http_request(url, method, data=None, params=None, **kwargs):
    param = ''
    if isinstance(params, dict):
        if '?' in url:
            old_query_str = url[:url.rfind('?')]
            url = url[url.rfind('?')+1:]
            query_dict = urlparse.parse_qs(old_query_str)
            query_dict.update(params)
        else:
            query_dict = params
        param = '?%s' % urllib.urlencode(query_dict) if query_dict else ''

    r = getattr(requests, method.lower())('%s%s' % (url, param), data=data)

    return r