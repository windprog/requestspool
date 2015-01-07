#RequestsPool
=========

##描述

    RequestsPool 是一个http请求转发代理,带有请求限速,缓存过期,外部缓存控制等功能的wsgi服务器.

##功能特点
* 请求限速: 例如:访问百度每10秒1次,就可以在在[示例配置](https://github.com/windprog/requestspool/blob/master/route_default.py)中的speed,配置如下:Speed(count_time=10000, limit_req=1)即可限速
* 缓存过期: 例如:同样在示例中,访问百度20秒后缓存过期,并且获取最新数据就可以这样配置: update=Update(20, True),异步获取可以这样配置update=Update(20, False)

##安装说明
首先下载源码，可以直接点击[download](https://github.com/windprog/requestspool/archive/master.zip)，也可以在shell下输入:
	
	git clone https://github.com/windprog/requestspool.git

安装pip：

    sudo apt-get install python-pip -y

httpappengine依赖gevent，先安装gevent依赖库：libevent

    sudo apt-get install python-dev gcc libevent-dev -y

安装virtualenv

    sudo pip install virtualenv

创建虚拟环境

    virtualenv env

保证硬盘有足够空间，cd到目录env中，执行

    cd env
    # 激活虚拟环境
    source bin/activate
    # 安装依赖包
    pip install -r ../requirements.txt

进入项目目录

    cd ../fastblog


运行

    python run.py

访问

    http://localhost:8801


#Done List
* 基于mongodb gridfs的缓存
* regex正则路由
* 访问限速

#TODO
* 基于文件系统的缓存
* 基于flask格式的路由
* 基于websocket的广播(通知下载完成等)与异地同步
* 远程获取配置信息