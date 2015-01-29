#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/29
Desc    :   
"""
from requestspool_client import patch_requests
import requests
patch_requests()

print len(requests.get("http://www.baidu.com").content)
