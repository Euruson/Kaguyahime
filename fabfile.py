# fabfile.py
import os, re
from datetime import datetime

# 导入Fabric API:
from fabric.api import *

# 服务器登录用户名:
env.user = 'root'
env.key_filename = 'D:\翻墙相关\id_rsa'

# 服务器地址，可以有多个，依次部署:
env.hosts = ['104.128.238.64']

# 服务器MySQL用户名和口令:
db_user = 'www-data'
db_password = '12345678'

_TAR_FILE = 'dist-kaguyahime.tar.gz'


def build():
    excludes = ['__pycache__', 'static/node_modules']
    local('del dist\\%s' % _TAR_FILE)
    with lcd(os.path.join(os.path.abspath('.'),'www')):
        cmd = ['tar', '--dereference', '-czvf', '../dist/%s' % _TAR_FILE]
        cmd.extend(['--exclude=%s' % ex for ex in excludes])
        cmd.extend(['.'])
        local(' '.join(cmd))


_REMOTE_TMP_TAR = '/home/www/kaguyahime/%s' % _TAR_FILE
_REMOTE_BASE_DIR = '/home/www/kaguyahime'


def deploy():
    newdir = 'www-%s' % datetime.now().strftime('%y-%m-%d_%H.%M.%S')
    # 删除已有的tar文件:
    run('rm -f %s' % _REMOTE_TMP_TAR)
    # 上传新的tar文件:
    put('dist/%s' % _TAR_FILE, _REMOTE_TMP_TAR)
    # 创建新目录:
    with cd(_REMOTE_BASE_DIR):
        run('mkdir %s' % newdir)
    # 解压到新目录:
    with cd('%s/%s' % (_REMOTE_BASE_DIR, newdir)):
        run('tar -xzvf %s' % _REMOTE_TMP_TAR)
    # 重置软链接:
    with cd(_REMOTE_BASE_DIR):
        run('rm -rf www')
        run('ln -s %s www' % newdir)
    # 重启Python服务和nginx服务器:
    with settings(warn_only=True):
        run('supervisorctl stop kaguyahime')
        run('supervisorctl start kaguyahime')