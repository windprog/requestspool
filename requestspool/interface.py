#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   
"""
from abc import ABCMeta, abstractmethod

#
# 接口调用规范。
#


class BaseSpeed(object):
    __metaclass__ = ABCMeta

    def add_one(self):
        pass


class BaseRoute(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def match(self, url):
        pass