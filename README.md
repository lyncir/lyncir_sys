Required:

* python >= 3.5
* gunicorn


## 目录结构


路径						| 描述						|
--------------------------- | --------------------------|
run.py						| 开发环境启动脚本			|
requirements.txt			| app依赖包文件。可以用dev,pro等隔离开发生产依赖文件 |
config.py					| app大部分配置变量,可分割为文件夹.例如default.py,production.py,development.py |
/instance/config.py			| 不需要在版本控制里的配置变量,例如数据库配置,密码配置,Debug.会覆盖config.py |
/app/						| 应用包					|
`/app/__init__.py`			| 初始文件					|
/app/views.py				| 路由定义,可分割为文件夹	|
/app/models.py				| 数据库表模型定义,可分割为文件夹 |


## 部署方式


* Gunicorn + Nginx Reverse Proxy


## 运行


```
$ python run.py

OR

$ gunicorn app:app --bind 0.0.0.0:8000 --workers 4 --worker-class sanic.worker.GunicornWorker
```
