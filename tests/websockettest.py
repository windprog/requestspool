#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/28
Desc    :   using  https://github.com/liris/websocket-client
            pip install websocket-client
"""
from gevent.monkey import patch_socket
patch_socket()
import time

import config
from requestspool.util import pdb_pm
from requestspool_client import Client


publish_config = {
    "match": [
        # 只监控百度的下载
        ".*baidu.com"
    ],
    "field": [
        # 以下为所有可用字段，可挑选
        "method", "url", "req_query_string", "req_headers", "req_data", "status_code", "res_headers", "res_data"
    ]
}

client = Client(port=config.PORT, config=publish_config)

while True:
    try:
        result = client.receive()
        print "url:%s data_len:%s" % (result.get("url"), len(result.get("res_data")))
    except:
        pdb_pm()
        print "等待1秒重试"
        time.sleep(1)
        client.reconnect()