#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/6
Desc    :   
"""
from importlib import import_module

DEBUG = True

# 服务器监听地址。
HOST = "0.0.0.0"
PORT = 8801

CACHE_TYPE = 'mongodbgridfs'
MONGODB_HOST = 'localhost'
MONGODB_PORT = 17117
MONGODB_DB_NAME = 'http_cache'
MONGODB_USER = 'test'
MONGODB_PW = 'test'
MONGODB_CACHE_COLL_NAME = 'cache'

# route的配置文件
ROUTE_MOD = 'route_default'

# 重新排序http query string 例如 c=1&b=3&d=1&a=9 参数和 a=9&c=1&b=3&d=1 参数是等效的.
RESORT_QUERY_STRING = True

# 载入项目根目录的配置文件
for name, val in vars(import_module('config')).iteritems():
    # 跳过内部对象
    if name.startswith("__") and name.endswith("__"):
        continue
    globals()[name] = val

# 以下配置不需要改变

# 需要载入的Action 模块
ACTIONS = [
    "requestspool.paction",
]