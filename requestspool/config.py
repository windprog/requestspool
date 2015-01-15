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
import os

DEBUG = True

# 服务器监听地址。
HOST = "0.0.0.0"
PORT = 8801

# 缓存类型
CACHE_TYPE = 'mongodbgridfs'
# mongodb地址
MONGODB_HOST = 'localhost'
# 端口
MONGODB_PORT = 17117
# 存放缓存的数据库名称
MONGODB_DB_NAME = 'http_cache'
# 用户名
MONGODB_USER = 'test'
# 密码
MONGODB_PW = 'test'
# 存放 gridfs 的 mongodb collection 名称
MONGODB_CACHE_COLL_NAME = 'cache'

# route的配置文件
ROUTE_MOD = 'route_default'

# 重新排序http query string 例如 c=1&b=3&d=1&a=9 参数和 a=9&c=1&b=3&d=1 参数是等效的.
RESORT_QUERY_STRING = True

# 默认缓存http计算类,存放地是httpinfo.py
DEFAULT_HTTPINFO_VERSION = "1"

# 运行临时文件
STUFF_PATH = os.path.join(os.path.realpath(os.path.dirname(__file__)), '..', 'stuff')
STUFF_LOG_PATH = os.path.join(STUFF_PATH, 'logs')
for path in (STUFF_PATH, STUFF_LOG_PATH,):
    if not os.path.exists(path):
        os.makedirs(path)

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