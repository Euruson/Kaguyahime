import logging.config
import asyncio
import os
import json
from aiohttp import web

def setup_logging(default_path = "conf/logging.json",default_level = logging.INFO):
    path = default_path
    if os.path.exists(path):
        with open(path,"r") as f:
            config = json.load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level = default_level)


## 定义服务器响应请求的的返回为 Kaguyahime"
async def index(request):
    return web.Response(body=b'<h1>Kaguyahime</h1>', content_type='text/html')


def init():
    ## 建立服务器应用，持续监听本地9000端口的http请求，对首页"/"进行响应
    app = web.Application()
    app.router.add_get('/', index)
    web.run_app(app, host='127.0.0.1', port=9000)


if __name__ == "__main__":
    setup_logging()
    init()
