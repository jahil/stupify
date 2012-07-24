from fabric.api import *
from fabric.colors import red, green, yellow, blue, _wrap_with
from fabric.utils import puts
from cuisine import *
from random import randint
from fabric.context_managers import hide
env.hosts = ["xxx.xxx.xxx.xxx"]
env.user ="root"
env.password = "password"
dbpasswd = "dbpasswd"
port =  randint(3307, 9999)
green_bg = _wrap_with('42')
red_bg = _wrap_with('41')

def uptime():
    run('uptime')

def create(account):
    """create new falkia account"""
    with settings(hide('running', 'user'), warn_only=True):
        print(green("bootstrapping falkia"))
        run("git clone git://github.com/jahil/falkia.git /falkia/%s" % account)
        print(green("creating database and user"))
        run('mysqladmin -u %s -p%s create %s' % (env.user, dbpasswd, account))
        run('mysql -u %s -p%s -e "grant all on %s.* to \'%s\'@\'localhost\' identified by \'DBM@rk3T\'"' % (env.user, dbpasswd, account, account))
    global naqsh
    naqsh = account
    init()

def init():
    """initialize account"""
#	print(green('Configuring Nginx'))
    print(green("setup/configure nginx"))
    file_write("/etc/nginx/sites-enabled/%s" % naqsh, text_strip_margin(
    """
    |server {
    |listen       80;
    |server_name  jahil.falkia.com;
    |
    |access_log  /var/log/nginx/jahil.access.log;
    |error_log /var/log/nginx/jahil.error.log;
    |location / {
    |proxy_pass         http://127.0.0.1:7777/;
    |proxy_redirect     off;
    |
    |proxy_set_header   Host             $host;
    |proxy_set_header   X-Real-IP        $remote_addr;
    |proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
    |proxy_max_temp_file_size 0;
    |
    |client_max_body_size       10m;
    |client_body_buffer_size    128k;
    |
    |proxy_connect_timeout      90;
    |proxy_send_timeout         90;
    |proxy_read_timeout         90;
    |
    |proxy_buffer_size          4k;
    |proxy_buffers              4 32k;
    |proxy_busy_buffers_size    64k;
    |proxy_temp_file_write_size 64k;
    |    }
    |}
    """
    ))
    with settings(hide('running', 'user'), warn_only=True):
        run('sed -i s/jahil/%s/g /etc/nginx/sites-enabled/%s' % (naqsh, naqsh))
        run('sed -i s/7777/%s/g /etc/nginx/sites-enabled/%s' % (port, naqsh))
        run('sed -i s/falkia/%s/g /falkia/%s/config/database.yml' % (naqsh, naqsh))
        run('sed -i s/3000/%s/g /falkia/%s/nbproject/project.properties' % (port, naqsh))
        print(green("database initialization"))
        run('mysql -u %s -p%s %s < /falkia/%s/extra/init.sql' % (env.user, dbpasswd, naqsh, naqsh))
        print(green("starting falkia instance"))
        run('cd /falkia/%s ; mongrel_rails start -p %s -a 127.0.0.1 -e production -P /tmp/%s.pid -d' % (naqsh, port, naqsh))
        run('/etc/init.d/nginx restart')
        print(red("ACCOUNT SETUP COMPLETED / ADD BELOW DNS RECORD TO YOUR DOMAIN"))
        print(green_bg('%s.falkia.com IN A 66.220.0.170') % naqsh )

def backup(account):
    """backup account and download"""
    with settings(hide('running', 'user'), warn_only=True):
        run('mysqldump -u %s -p%s %s | gzip > /tmp/%s.sql.gz' % (env.user, dbpasswd, account, account))
        get('/tmp/%s.sql.gz' %account)
        run('rm -fr /tmp/%s.sql.gz' %account)

def accounts():
    """list available accounts"""
    with settings(hide('everything', 'commands'), warn_only=True):
        accounts = run('ls /falkia')
        lists = accounts.split()
        print (green(lists))

def delete(account):
    """delete account without backup"""
    with settings(hide('everything', 'commands'), warn_only=True):
        stop(account)
        print(yellow("[*] removing files"))
        run('rm -fr /falkia/%s' % account)
        print(yellow("[*] dropping database"))
        run('mysql -u %s -p%s -e "drop database %s"' % (env.user, dbpasswd, account))
        print(yellow("[*] dropping database user"))
        run('mysql -u %s -p%s -e "drop user %s@localhost"' % (env.user, dbpasswd, account))
        print(yellow("[*] removing nginx configuration"))
        run('rm -fr /etc/nginx/sites-enabled/%s' % account)
        run('/etc/init.d/nginx restart')
        print(red_bg("[*] %s account deleted") % account)

def restart(account):
    """restart falkia instance on account"""
    stop(account)
    start(account)

def stop(account):
    """stop falkia instance on account"""
    with settings(hide('everything', 'commands'), warn_only=True):
        run ('cd /falkia/%s ; mongrel_rails stop -P /tmp/%s.pid' % (account, account))
        print(yellow("* falkia instance stopped on %s") % account)

def start(account):
    """start falkia instance on account"""
    with settings(hide('everything', 'commands'), warn_only=True):
        nport = run('cat /etc/nginx/sites-enabled/%s | grep ":" | cut -c 37-40' % account)
        run ('cd /falkia/%s ; mongrel_rails start -p %s -a 127.0.0.1 -e production -P /tmp/%s.pid -d' % (account, nport, account))
        #pid = run('cat /tmp/%s.pid' % account)
        #print(green("* falkia instance started on %s with PID: %s") % (account, pid))
        print(green("* falkia instance started on %s") % account)

def getport(account):
    with settings(hide('everything', 'commands'), warn_only=True):
        nport = run('cat /etc/nginx/sites-enabled/%s | grep ":" | cut -c 37-40' % account)
        print (green(nport))


def pidof(account):
    """show account process id """
    with settings(hide('everything', 'commands'), warn_only=True):
        pid = run('cat /tmp/%s.pid' % account)
        print(green("* %s pid is: %s") % (account, pid))
