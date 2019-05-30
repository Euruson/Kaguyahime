import asyncio, time
import os
import json
from aiohttp import web
from jinja2 import Environment, FileSystemLoader
import logging.config
from types import SimpleNamespace

import orm
import coroweb
from middleware import logger_factory, data_factory, response_factory
from jinja_filter import datetime_filter

## handlers 是url处理模块, 当handlers.py在API章节里完全编辑完再将下一行代码的双井号去掉
## from handlers import cookie2user, COOKIE_NAME


def init_logging(  # 初始化日志配置
        default_path="conf/logging.json", default_level=logging.INFO):
    path = default_path
    if os.path.exists(path):
        with open(path, "r") as f:
            config = json.load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def init_jinja2(app, **kw):  # 初始化jinja2的函数
    logging.info('init jinja2...')
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True))
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env


async def init(loop):  # 初始化服务器
    init_logging()
    with open('conf/conf.json', 'r') as f:
        configs = json.load(f, object_hook=lambda d: SimpleNamespace(**d))
    await orm.create_pool(loop=loop, **configs.db.__dict__)
    ## 在handlers.py完全完成后,在下面middlewares的list中加入auth_factory
    app = web.Application(
        loop=loop, middlewares=[logger_factory, response_factory])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    coroweb.add_routes(app, 'handler')
    coroweb.add_static(app)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('Kaguyahime started at http://127.0.0.1:9000...')
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
