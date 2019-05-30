from aiohttp import web
import logging
import json

middlerware_logger = logging.getLogger("MIDDLEWARE")


## 以下是middleware,可以把通用的功能从每个URL处理函数中拿出来集中放到一个地方
## URL处理日志工厂
async def logger_factory(app, handler):

    async def logger(request):
        middlerware_logger.info(
            'Request: %s %s' % (request.method, request.path))
        return (await handler(request))

    return logger


## 认证处理工厂--把当前用户绑定到request上，并对URL/manage/进行拦截，检查当前用户是否是管理员身份
## 需要handlers.py的支持, 当handlers.py在API章节里完全编辑完再将下面代码的双井号去掉
##async def auth_factory(app, handler):
##    async def auth(request):
##        middlerware_logger.info('check user: %s %s' % (request.method, request.path))
##        request.__user__ = None
##        cookie_str = request.cookies.get(COOKIE_NAME)
##        if cookie_str:
##            user = await cookie2user(cookie_str)
##            if user:
##                middlerware_logger.info('set current user: %s' % user.email)
##                request.__user__ = user
##        if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin):
##            return web.HTTPFound('/signin')
##        return (await handler(request))
##    return auth


## 数据处理工厂
async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                middlerware_logger.info(
                    'request json: %s' % str(request.__data__))
            elif request.content_type.startswith(
                    'application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                middlerware_logger.info(
                    'request form: %s' % str(request.__data__))
        return (await handler(request))

    return parse_data


## 响应返回处理工厂
async def response_factory(app, handler):
    async def response(request):
        middlerware_logger.info('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(
                    body=json.dumps(
                        r, ensure_ascii=False, default=lambda o: o.__dict__).
                    encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                ## 在handlers.py完全完成后,去掉下一行的双井号
                ##r['__user__'] = request.__user__
                resp = web.Response(
                    body=app['__templating__'].get_template(template).render(
                        **r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(status=r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(status=t, reason=str(m))
        # default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp

    return response
