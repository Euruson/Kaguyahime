import re
import time
import json
import logging
import hashlib
import base64
import asyncio
import markdown
from aiohttp import web
from coroweb import get, post
import os

# 分页管理以及调取API时的错误信息
from apis import Page, APIValueError, APIResourceNotFoundError, APIPermissionError, APIError
from model import User, Comment, Blog, BlogTag, Tag, next_id
from types import SimpleNamespace
from orm import StringField

with open('conf/conf.json', 'r') as f:
    configs = json.load(f, object_hook=lambda d: SimpleNamespace(**d))

COOKIE_NAME = 'Kaguyahime'
_COOKIE_KEY = configs.session.secret
_INVITATION_KEY = configs.session.key


# 查看是否是管理员用户
def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()


# 获取页码信息
def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p


# 计算加密cookie
def user2cookie(user, max_age):
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


# 文本转HTML
def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<',
                                                                        '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)


# 生成TOC
def toc_parser(toc_tokens):
    html = ''
    for token in toc_tokens:
        html += '<li><a href="#%s">%s</a>' % (token['id'], token['name'])
        if (token['children']):
            html = html + '<ul class="uk-nav-sub">' + toc_parser(
                token['children']) + '</ul>'
        html += '</li>'
    return html


def toc_helper(toc_tokens):
    if toc_tokens:
        return '<div uk-sticky="offset: 200" class="toc"> 文章目录<br> Table of Contents<br><br>' +\
            '<ul  class="uk-nav uk-nav-default" uk-scrollspy-nav="closest: li; scroll: true; offset: 100; cls: toc-active">' +\
            toc_parser(toc_tokens) +\
            '</ul></div>'


# 解密cookie
async def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None


# 处理首页URL
@get('/')
async def index(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = await Blog.findAll(
            orderBy='created_at desc', limit=(p.offset, p.limit))
        for blog in blogs:
            blog_tags = await BlogTag.findAll("`blog_id`=?", [blog.id])
            blog.tags = []
            for blog_tag in blog_tags:
                blog.tags.append(
                    dict(
                        blog_tag=blog_tag, tag=await
                        Tag.find(blog_tag.tag_id)))
    return {'__template__': 'blogs.html', 'page': p, 'blogs': blogs}


# 处理日志详情页面URL
@get('/blog/{id}')
async def get_blog(id):
    blog = await Blog.find(id)
    comments = await Comment.findAll(
        'blog_id=?', [id], orderBy='created_at desc')

    # 处理博客和评论markdown渲染
    md = markdown.Markdown(extensions=['extra', 'toc', 'mdx_math'])
    blog.html_content = md.convert(blog.content)
    blog.toc = toc_helper(md.toc_tokens)
    for c in comments:
        c.html_content = markdown.markdown(c.content)

    # 处理博客tag
    blog_tags = await BlogTag.findAll("`blog_id`=?", [blog.id])
    blog.tags = []
    for blog_tag in blog_tags:
        blog.tags.append(
            dict(blog_tag=blog_tag, tag=await Tag.find(blog_tag.tag_id)))

    return {'__template__': 'blog.html', 'blog': blog, 'comments': comments}


# 处理标签页汇总URL
@get('/tags')
async def get_all_tags():
    tags = await Tag.findAll()
    for tag in tags:
        tag.num = await BlogTag.findNumber('count(id)', "`tag_id`=?", [tag.id])
    return {'__template__': 'tags.html', 'tags': tags}


# 处理标签页URL
@get('/tag/{name}')
async def get_blogs_of_tag(name, *, page='1'):
    tag = await Tag.findAll("`name`=?", [name])
    page_index = get_page_index(page)
    num = await BlogTag.findNumber('count(id)', "`tag_id`=?", [tag[0].id])
    p = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = []
        tag_blogs = await BlogTag.findAll(
            "`tag_id`=?", [tag[0].id], limit=(p.offset, p.limit))
        for tag_blog in tag_blogs:
            blogs.append(await (Blog.find(tag_blog.blog_id)))
        blogs = sorted(blogs, key=lambda x: x.created_at, reverse=True)

        for blog in blogs:
            blog_tags = await BlogTag.findAll("`blog_id`=?", [blog.id])
            blog.tags = []
            for blog_tag in blog_tags:
                blog.tags.append(
                    dict(
                        blog_tag=blog_tag, tag=await
                        Tag.find(blog_tag.tag_id)))
    return {'__template__': 'blogs.html', 'page': p, 'blogs': blogs}


# 处理注册页面URL
@get('/register')
def register():
    return {'__template__': 'register.html'}


# 处理登录页面URL
@get('/signin')
def signin():
    return {'__template__': 'signin.html'}


# 用户登录验证API
@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(
        COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


# 用户注销
@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r


# 获取管理页面
@get('/manage/')
def manage():
    return 'redirect:/manage/comments'

# 上传文件页面
@get('/manage/upload')
def upload():
    return {'__template__': 'manage_upload.html'}

# 评论管理页面
@get('/manage/comments')
def manage_comments(*, page='1'):
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }


# 日志管理页面
@get('/manage/blogs')
def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }


# 创建日志页面
@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }


# 编辑日志页面
@get('/manage/blogs/edit')
def manage_edit_blog(*, id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs/%s' % id
    }


# 用户管理页面
@get('/manage/users')
def manage_users(*, page='1'):
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }


# 获取评论信息API
@get('/api/comments')
async def api_comments(*, page='1'):
    page_index = get_page_index(page)
    num = await Comment.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(
        orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)


# 用户发表评论API
@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(
        blog_id=blog.id,
        user_id=user.id,
        user_name=user.name,
        user_image=user.image,
        content=content.strip())
    await comment.save()
    return comment


# 管理员删除评论API
@post('/api/comments/{id}/delete')
async def api_delete_comments(id, request):
    check_admin(request)
    c = await Comment.find(id)
    if c is None:
        raise APIResourceNotFoundError('Comment')
    await c.remove()
    return dict(id=id)


# 获取用户信息API
@get('/api/users')
async def api_get_users(*, page='1'):
    page_index = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = await User.findAll(
        orderBy='created_at desc', limit=(p.offset, p.limit))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)


# 定义EMAIL和HASH的格式规范
_RE_EMAIL = re.compile(
    r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


# 用户注册API
@post('/api/users')
async def api_register_user(*, email, name, passwd, key):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    if key != _INVITATION_KEY:
        raise APIError('register:failed', 'invitation-code',
                       'Invalid invitation code')
    users = await User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(
        id=uid,
        name=name.strip(),
        email=email,
        passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
        image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(
            email.encode('utf-8')).hexdigest())
    await user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(
        COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


# 获取日志列表API
@get('/api/blogs')
async def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(
        orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)


# 获取日志详情API
@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    blog = await Blog.find(id)
    return blog


# 发表日志API
@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content, selectedTags):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(
        user_id=request.__user__.id,
        user_name=request.__user__.name,
        user_image=request.__user__.image,
        name=name.strip(),
        summary=summary.strip(),
        content=content.strip())
    await blog.save()
    for selectedTag in selectedTags:
        if (selectedTag['key']):
            blog_tag = BlogTag(blog_id=blog.id, tag_id=selectedTag['key'])
            await blog_tag.save()
        else:
            tag = Tag(name=selectedTag['value'])
            await tag.save()
            blog_tag = BlogTag(blog_id=blog.id, tag_id=tag.id)
            await blog_tag.save()
    return blog


# 编辑日志API
@post('/api/blogs/{id}')
async def api_update_blog(id, request, *, name, summary, content,
                          selectedTags):
    check_admin(request)
    blog = await Blog.find(id)
    blog_tags = await BlogTag.findAll("`blog_id`=?", [id])
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()

    # for selectedTag in selectedTags:
    #     if selectedTag['key']=='':
    #         tag = Tag(name=selectedTag['value'])
    #         await tag.save()
    #         blog_tag = BlogTag(blog_id=blog.id,tag_id=tag.id)
    #         await blog_tag.save()
    #         selectedTags.remove(selectedTag)

    for blog_tag in blog_tags:
        for selectedTag in selectedTags:
            if blog_tag.id == selectedTag['key']:
                blog_tags.remove(blog_tag)
                selectedTags.remove(selectedTag)

    for selectedTag in selectedTags:
        if (selectedTag['key']):
            blog_tag = BlogTag(blog_id=blog.id, tag_id=selectedTag['key'])
            await blog_tag.save()
        else:
            tag = Tag(name=selectedTag['value'])
            await tag.save()
            blog_tag = BlogTag(blog_id=blog.id, tag_id=tag.id)
            await blog_tag.save()

    tags = []
    for blog_tag in blog_tags:
        tags.append(await Tag.find(blog_tag.tag_id))
    for tag in tags:
        if (await BlogTag.findNumber('count(id)', "`tag_id`=?",
                                     [tag.id])) == 1:
            await tag.remove()
    for blog_tag in blog_tags:
        await blog_tag.remove()

    return blog


# 删除日志API
@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
    check_admin(request)
    blog = await Blog.find(id)
    blog_tags = await BlogTag.findAll("`blog_id`=?", [id])
    tags = []
    for blog_tag in blog_tags:
        tags.append(await Tag.find(blog_tag.tag_id))
    for tag in tags:
        if (await BlogTag.findNumber('count(id)', "`tag_id`=?",
                                     [tag.id])) == 1:
            await tag.remove()
    for blog_tag in blog_tags:
        await blog_tag.remove()
    await blog.remove()
    return dict(id=id)


# 删除用户API
@post('/api/users/{id}/delete')
async def api_delete_users(id, request):
    check_admin(request)
    id_buff = id
    user = await User.find(id)
    if user is None:
        raise APIResourceNotFoundError('Comment')
    await user.remove()
    # 给被删除的用户在评论中标记
    comments = await Comment.findAll('user_id=?', [id])
    if comments:
        for comment in comments:
            id = comment.id
            c = await Comment.find(id)
            c.user_name = c.user_name + ' (该用户已被删除)'
            await c.update()
    id = id_buff
    return dict(id=id)


# 获取所有Tag名称 API
@get('/api/tags')
async def api_get_tags():
    tags = await Tag.findAll()
    return dict(tags=tags)


# 获取Tag及其文章 API
@get('/api/tags/{id}')
async def api_get_tag(*, id):
    if re.match(r'[0-9a-zA-Z\_]{50}', id):
        tag = await Tag.findAll("id=?", [id])
    else:
        tag = await Tag.findAll("name=?", [id])
    if tag:
        tag[0].blogs = list(
            map(lambda x: x.blog_id, await BlogTag.findAll(
                "`tag_id`=?", [tag[0].id])))
    return tag


# 删除Tag API
@post('/api/tags/{id}/delete')
async def api_delete_tag(request, *, id):
    check_admin(request)
    if re.match(r'[0-9a-zA-Z\_]{50}', id):
        tag = await Tag.findAll("id=?", [id])
    else:
        tag = await Tag.findAll("name=?", [id])
    tag_blogs = BlogTag.findAll("tag_id=?", [tag.id])
    for tag_blog in tag_blogs:
        await tag_blog.remove()
    await tag.remove()
    return dict(id=id)


# 添加TAG API
@post('/api/tags')
async def api_create_tag(request, *, name):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    tag = Tag(name=name.strip())
    await tag.save()
    return tag


# 修改TAG API
@post('/api/tags/{id}')
async def api_update_tag(id, request, *, name):
    check_admin(request)
    tag = await Tag.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    tag.name = name.strip()
    await tag.update()
    return tag


# 获取博客TAG API
@get('/api/blog-tag/{id}')
async def api_get_blog_tag(*, id):
    blog_tags = await BlogTag.findAll("`blog_id`=?", [id])
    tags = []
    for blog_tag in blog_tags:
        tags.append(await Tag.find(blog_tag.tag_id))
    return dict(tags=tags)


# 修改博客TAG API
@post('/api/blog-tag/{id}')
async def api_update_blog_tag(id, request, *, tags):
    check_admin(request)
    blog_tags = await BlogTag.findAll("`blog_id`=?", [id])
    pre_tags = []
    for blog_tag in blog_tags:
        pre_tags.append(await Tag.find(blog_tag.tag_id))


# 上传文件API
@post('/api/upload')
async def api_upload_file(request):
    check_admin(request)
    reader = await request.multipart()
    await reader.next()
    upload_file = await reader.next()
    filename = upload_file.filename
    fdir = configs.upload.linux if os.name == 'posix' else configs.upload.windows
    ftype = os.path.splitext(filename)[-1]
    print(ftype)
    if ftype in {'.jpg','.jpeg','.png','.gif'}:
        filename = next_id()+ftype

    size = 0
    with open(os.path.join(fdir, filename), 'wb') as f:
        while True:
            chunk = await upload_file.read_chunk()
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)
    return '{} sized of {} successfully stored'.format(filename, size)
