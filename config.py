#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   详细配置说明请参考httpappengine/engine/config.py
"""
DEBUG = True

# 服务器监听地址。
HOST = "0.0.0.0"
PORT = 8801

# 需要载入的Action 模块
ACTIONS = [
    "action",
]

CACHE_TYPE = 'mongodbgridfs'
MONGODB_HOST = 'localhost'
MONGODB_PORT = 17117
MONGODB_DB_NAME = 'http_cache'
MONGODB_USER = 'test'
MONGODB_PW = 'test'
MONGODB_CACHE_COLL_NAME = 'cache'

from requestspool.route import RegexRoute, Speed
from requestspool.update import Update
ROUTE_URL = [
    RegexRoute(pattern=u".*?/soccer/get_", speed=Speed(count_time=1000*10, limit_req=100), update=Update(24*60*60, False)),
    # 百度每10秒访问一次
    RegexRoute(pattern=u"http://www.baidu.com.*", speed=Speed(count_time=1000*10, limit_req=1), update=Update(100, False)),
    # 代理请求
    RegexRoute(pattern=u".*"),
]
