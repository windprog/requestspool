#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/20
Desc    :   
"""
import gevent
from gevent.event import AsyncResult

from requestspool.route import HttpEvent


a = HttpEvent()

def setter():
    """
    After 3 seconds set the result of a.
    """
    gevent.sleep(3)
    a.value = 'Hello!'


def waiter():
    """
    After 3 seconds the get call will unblock after the setter
    puts a value into the AsyncResult.
    """
    print a.value


gevent.joinall([
    gevent.spawn(setter),
    gevent.spawn(waiter),
    gevent.spawn(waiter),
    gevent.spawn(waiter),
])
