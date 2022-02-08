[izone](https://github.com/Hopetree/izone) 博客容器部署方案

## step_01：准备镜像
项目部署需要3个基础镜像外加一个izone的构建镜像（可以自己拉取代码构建，不过这里推荐拉取我构建好的镜像），拉取镜像的命令：
```
# 3个基础镜像
docker pull nginx
docker pull redis
docker pull mysql:5.7
# 1个自构建镜像，这个tag表示19年7月构建，项目是第3代，镜像对应的编排版本也使用这个tag，后续会说到
docker pull registry.cn-shenzhen.aliyuncs.com/tendcode/izone:3.19.7
```

## step_02：拉取项目代码
为了避免挂载目录权限问题，后续命令全部使用root账号执行。

拉取代码，直接拉取跟镜像的tag一样的项目tag：
```
git clone -b 3.19.7 https://github.com/Hopetree/izone-docker.git
```

## step_03：创建环境变量文件
项目依赖两个环境变量文件，必须创建，第一个文件是 .env，这个文件是docker-compose 默认使用的环境变量问题，可以把参数传递到 docker-compose 中。进入izone-docker 目录，创建两个问题，文件内容如下：
```
# .env

# db
MYSQL_IMAGE=mysql:5.7
MYSQL_ROOT_PASSWORD=1314520@abc

# redis
REDIS_IMAGE=redis

# web
IZONE_IMAGE=registry.cn-shenzhen.aliyuncs.com/tendcode/izone:3.19.7
IZONE_MYSQL_NAME=izone

# nginx
NGINX_IMAGE=nginx
```

然后创建一个 izone.env 文件，这个里面的环境变量都会传递给 izone 使用，至于izone 可以设置哪些环境变量，可以去 izone 项目的 settings 文件中查看。这里可以虽然传入几个变量（其实可以一个也不传，因为环境变量不传的时候有默认值使用）：

```
# izone.env

# 个性化配置
IZONE_SECRET_KEY=#!kta!9e0)24p@9#=*=ra$r!0k0+p5@w+a%7g1bboo9+9080
IZONE_TOOL_FLAG=True
IZONE_API_FLAG=False
IZONE_DEBUG=False
IZONE_SITE_END_TITLE=izone
IZONE_SITE_DESCRIPTION=izone 博客
IZONE_SITE_KEYWORDS=Python自学,Python爬虫,Django博客,Python web开发,个人博客
IZONE_GITHUB=https://github.com/Hopetree

# 邮箱配置
IZONE_EMAIL_HOST=smtp.163.com
IZONE_EMAIL_HOST_USER=your-email
IZONE_EMAIL_HOST_PASSWORD=77777
IZONE_EMAIL_PORT=465
IZONE_EMAIL_USE_SSL=True
IZONE_DEFAULT_FROM_EMAIL=izone博客 <test@163.com>
IZONE_ACCOUNT_EMAIL_VERIFICATION=optional

# 非必须设置
IZONE_CNZZ_PROTOCOL=''
IZONE_BEIAN=''
IZONE_SITE_VERIFICATION=''

# 配置管理员邮箱，格式：name|test@test.com 多组用户用英文逗号隔开
IZONE_ADMIN_EMAIL_USER=name|test@test.com
```

两个文件创建成功之后可以检查一下文件是合格，执行命令：
```
docker-compose config
```
没有报错就说明格式没问题，可以查看一下环境变量是否传错

## step_04：修改 nginx配置
由于项目默认给的nginx配置是我自己项目的，所以不适合其他人使用，这里把项目代码中nginx/conf.d/ 目录中的配置文件全部删除，然后在nginx/conf.d/ 目录中创建一个通用的配置（使用 localhost）：
```
cd nginx/conf.d && rm -f server_izone.conf
vi default.conf
```
default.conf 的内容如下：
```
server {
    # 端口和域名
    listen 80;
    server_name localhost;

    # static 和 media 的地址
    location /static/ {
        root /opt/izone;
    }
    location /media/ {
        root /opt/izone;
    }

    # web 服务使用80端口，并且添加别名跟本地域名保持一致
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 其他配置
    client_max_body_size 1m;
    client_header_buffer_size 128k;
    client_body_buffer_size 1m;
    proxy_buffer_size 32k;
    proxy_buffers 64 32k;
    proxy_busy_buffers_size 1m;
    proxy_temp_file_write_size 512k;
}
```

## step_05：部署容器
退回到 izone-docker 目录，启动容器的命令（加 -d 是后台运行），可以看到输出：
```
[root@CentOS-2 izone-docker]# docker-compose up -d
Creating network "izone-docker_frontend" with driver "bridge"
Creating network "izone-docker_backend" with driver "bridge"
Creating izone_redis ... done
Creating izone_db    ... done
Creating izone_web   ... done
Creating izone_nginx ... done
```

然后可以查看一下容器运行状态，如果都是up 就没问题：
```
[root@CentOS-2 izone-docker]# docker-compose ps
   Name                  Command               State                    Ports
-----------------------------------------------------------------------------------------------
izone_db      docker-entrypoint.sh mysqld      Up      3306/tcp, 33060/tcp
izone_nginx   nginx -g daemon off;             Up      0.0.0.0:443->443/tcp, 0.0.0.0:80->80/tcp
izone_redis   docker-entrypoint.sh redis ...   Up      6379/tcp
izone_web     gunicorn izone.wsgi -b 0.0 ...   Up
```
## step_06：初始化数据库
虽然容器都起来了，但是izone 项目的数据库里面是空的，所以要先初始化一下数据库，直接在izone-docker 目录下执行如下命令：
```
# 一条一条的输入
# 初始化数据
docker exec -it izone_web python manage.py makemigrations
docker exec -it izone_web python manage.py migrate
# 收集静态文件
docker exec -it izone_web python manage.py collectstatic
# 初始化搜索索引
docker exec -it izone_web python manage.py update_index
# 创建管理员账号
docker exec -it izone_web python manage.py createsuperuser
```

## step7：重启服务，浏览页面
在izone-docker 目录下，依次执行关闭和启动命令，重启服务：
```
[root@CentOS-2 izone-docker]# docker-compose down
Stopping izone_nginx ... done
Stopping izone_web   ... done
Stopping izone_redis ... done
Stopping izone_db    ... done
Removing izone_nginx ... done
Removing izone_web   ... done
Removing izone_redis ... done
Removing izone_db    ... done
Removing network izone-docker_frontend
Removing network izone-docker_backend
[root@CentOS-2 izone-docker]# docker-compose up -d
Creating network "izone-docker_frontend" with driver "bridge"
Creating network "izone-docker_backend" with driver "bridge"
Creating izone_redis ... done
Creating izone_db    ... done
Creating izone_web   ... done
Creating izone_nginx ... done
```

浏览器输入服务器（或者虚拟机）的IP地址查看页面是否正常，也可以在服务器使用curl 命令访问:
```
curl http://localhost
```
浏览器效果：
![image](https://user-images.githubusercontent.com/30201215/61143465-ea3f9b00-a504-11e9-9b26-f8c3f94e372f.png)

要升级部署的项目，可以去看文章 [容器化部署博客（3）—— 更换服务器，5分钟完成项目迁移](https://tendcode.com/article/docker-rebuild/)

