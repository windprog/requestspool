#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/18
Desc    :   
"""
from multiprocessing import Process
import os
from multiprocessing import Value, Array

def worker(num, mystr, arr):
    num.value *= 2
    mystr.value = str(os.getpid())

    for i in range(len(arr)):
        arr[i] = arr[i] * -1 + 1.5

def dump_vars(num, mystr, arr):
    print 'num: ', num.value
    print 'str: ', mystr[:]
    print 'arr: ', arr[:]

def test_sharedmemory():
    num = Value('i', 5)
    mystr = Array('c', 'just for test')
    arr = Array('d', [1.0, 1.5, -2.0])

    print 'init value'
    dump_vars(num, mystr, arr)

    ps = [Process(target=worker, args=(num, mystr, arr)) for _ in range(3)]
    for p in ps:
        p.start()
    for p in ps:
        p.join()

    print
    print 'after all workers finished'
    dump_vars(num, mystr, arr)

if __name__=='__main__':
    test_sharedmemory()