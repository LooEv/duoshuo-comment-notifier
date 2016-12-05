## 介绍
如果你的博客使用了多说评论，那么很不幸，你的博客有了新留言你收不到提醒。多说评论系统设定的是只有别人回复了你的留言才会邮件通知你。虽然刚开始写博客的时候，给我们留言的人很少，或者也许以后也没有多少留言（**此处应该有一个笑哭的表情**，此刻看看窗外，那只猫也在嘲笑我），不过如果有人给我们留言了，那我们及时回复他也是一种尊重他的表现，所以用 python 编写了一个脚本解决多说评论的不完美提醒。<!-- more -->

## Requirement
* **python 2.7** 以及 **python 3** 都可运行；
* 此脚本只用到 `requests` 这一个第三方库，请安装：
```bash
pip install requests
```

## 实现原理
这是获取 [多说评论后台操作日志](http://dev.duoshuo.com/docs/50037b11b66af78d0c000009) 的官方说明。通过 `requests` 获取博客的评论日志，判断是否产生了新的日志，然后进一步判断是否是别人的评论或者回复（因为你自己回复别人也会产生操作日志），如果条件成立，则发送邮件；否则，等待下一次 check。另外，如果在脚本运行过程中出现问题，脚本会将错误信息以邮件的形式发送给我们，以便我们及时处理。

## 效果展示
如果新评论数 <= 20，那么显示详细的评论信息，效果如下：
![效果展示1](http://ocf3ikxr2.bkt.clouddn.com/python/duoshuo_comments.png)

如果新评论数 > 20，就只是提示功能（显示过多反而不好），如下：
![效果展示2](http://ocf3ikxr2.bkt.clouddn.com/python/duoshuo_comments2.png)

-----
## 配置文件 (_config.conf)
```
[duoshuo_account]
short_name = 你在多说评论站点注册的多说二级域名
secret = 站点密钥
myself_author_id = 你的多说id，用于剔除自己给别人的回复提醒（这个id不好找，希望你能找到）
myself_author_url = 你的个人主页

[email_info]
email_host = smtp.xxx.com	# 请确保你的邮箱开启了SMTP服务
from_address = 发生邮件的邮箱地址
email_password = 邮箱密码
to_address = 接收邮件的邮箱地址

[period_of_check]
period = xxx （检查是否有新评论的间隔周期，单位秒）
```
**说明**：if 你有一台 vps，可以使用 crontab 设置定时任务更为方便

elif 你没有 vps，使用的是 Windows，那么只能使用 Windows 自带的创建计划任务功能开机自运行脚本，此时就需要 `period_of_check` 这个配置。

## 使用方法
**第一步**：
```bash
git clone https://github.com/LooEv/duoshuo-comment-notifier.git ~/duoshuo-comment-notifier

chmod +x ~/duoshuo-comment-notifier/comment_notifier.py	#这一步很重要！
```
然后编辑 `_config.conf` 文件，将自己的配置信息填写完整。

**第二步，设置定时运行脚本**：
在 Linux中，运行下面的命令：
```bash
crontab -e	# 编辑当前用户的crontab文件
```
添加下面的内容：
```bash
0,30 8-23 * * * /usr/bin/env python ~/duoshuo-comment-notifier/comment_notifier.py >/dev/null 2>&1
# 每天8点到23点之间每隔30分钟执行脚本

* 8-23/1 * * * /usr/bin/env python ~/duoshuo-comment-notifier/comment_notifier.py >/dev/null 2>&1
# 或者每天8点到23点之间每隔1小时执行脚本

* 8-23/5 * * * /usr/bin/env python ~/duoshuo-comment-notifier/comment_notifier.py >/dev/null 2>&1
# 或者每天8点到23点之间每隔5小时执行脚本
```
视自己的情况而定，选择适当的间隔周期执行脚本。
`>/dev/null 2>&1` 表示将脚本的标准输出流和标准错误流都不显示（不用担心，脚本设置的日志文件依然会产生，以便我们发现问题所在），防止 crontab 产生的日志文件过大。
**注意**：如果你正在使用多个版本的 python，请自行修改上面代码中的 `/usr/bin/env python`，尽量将执行这个脚本的python的路径定死，并确保该python版本环境下安装了所需的第三方库。
在Windows系统中开机自启动脚本的方法这里就不介绍了，请自行 google。

## 实现细节
### 兼容python2和3
```python
try:
    from ConfigParser import ConfigParser
except:
    from configparser import ConfigParser

if sys.version_info[0] >= 3:
    unicode = str
    xrange = range
```

### 全局说明
```python
config = {}
dir_name = os.path.dirname(os.path.abspath(__file__))
config_file = dir_name + os.sep + '_config.conf'
action_counter_file = dir_name + os.sep + 'action_counter.log'
duoshuo_url = 'http://duoshuo.com/'

# log_url 用于获取多说评论后台操作日志，所有的评论都包括在里面
# article_info_url 可以获取指定的某一篇文章的评论，此脚本用于获取该文章的标题
template = {
    'log_url':
        "http://api.duoshuo.com/log/list.json?order=desc&short_name=%(short_name)s&secret=%(secret)s&limit=200",
    'article_info_url':
        "http://api.duoshuo.com/threads/listPosts.json?thread_key=%s&short_name=%s&page=1&limit=10",
    'comment_info':
        u"""用户昵称：%(author_name)s
            IP地址：  %(ip)s
            用户网站：%(author_url)s
            评论文章：%(thread_key)s
            评论时间：%(created_at)s
            评论内容：%(message)s"""
}
```

### 函数说明
* **get_config()：获取配置**

* **设置日志器**
```python
class BufferingSMTPHandler(logging.handlers.BufferingHandler):
    def __init__(self, capacity):
        logging.handlers.BufferingHandler.__init__(self, capacity)
        self.setFormatter(logging.Formatter(
            u'%(asctime)s - %(levelname)-5s - 函数名：%(funcName)s - 行号：%(lineno)d - %(pathname)s - 信息：\n%(message)s'))

    def flush(self):
        self.acquire()
        content = ''
        try:
            if len(self.buffer) > 0:
                content = map(self.format, self.buffer)
                self.buffer = []
        except Exception as e:
            logger.exception(e)
        finally:
            if content:
                send_email('\n\n'.join(content))
            self.release()
            del content

def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    log_name = (dir_name + os.sep + 'notifier.log')
    fh = logging.FileHandler(filename=log_name)
    fh.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    log_send = BufferingSMTPHandler(10)
    log_send.setLevel(logging.ERROR)
    logger.addHandler(log_send)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
```
  为了方便调试，我设置了日志器，此日志器既可以在标准输出流中输出，也可以将 ERROR 级别的日志记录在 notifier.log 文件中，还可以通过邮件发送 ERROR 级别的日志，`BufferingSMTPHandler` 是我以 `logging.handlers.BufferingHandler` 创建的子类。当然也可以使用 `logging.handlers.SMTPHandler`， 不过会出现一个问题，就是有几条 ERROR 级别的日志，它就会给你发送几封邮件，这是我们不想要的结果，我们需要的是汇总邮件，一封就够。定义 `BufferingSMTPHandler` 的好处是如果因为某些原因导致脚本运行失败我们能够及时知道并处理。如果有不明白的地方，建议看 [logging.handlers](https://hg.python.org/cpython/file/2.7/Lib/logging/handlers.py) 的源码。

* **获取多说评论后台日志**
```python
def get_duoshuo_log(url):
    first = False
    if os.path.isfile(action_counter_file):
        f = open(action_counter_file)
        last_counter = int(f.read())
    else:
        logger.debug(u'没有找到action_counter.log文件，我假设你博客的留言你已经全部看过，也就是没有新留言！')
        last_counter = 0
        first = True
    try:
        req = requests.get(url, timeout=10)
        data = req.json()
        if data['code'] == 0:
            logger.debug(u'获取多说评论后台操作日志成功')
            counter = len(data['response'])
            if counter == 0:
                return
            if last_counter != counter:
                with open(action_counter_file, 'w') as f:
                    f.write(str(counter))
                if first:
                    return
                return data, last_counter, counter
    except Exception as e:
        logger.exception(e)
```
  action_counter_file 文件是记录上一次运行脚本检查到的你的多说评论后台有多少个评论操作数，包括别人给你的评论和回复，你给别人的回复，以及你删除评论的操作总次数。通过判断日志操作数是否发生变化得知是否有新的操作动态。

* **处理评论日志并生成邮件内容**
```python
def email_content(comment_count, metas):
    header = u'你有%d条新评论' % comment_count
    log_msg = header + u'，正在生成邮件内容'
    logger.debug(log_msg)
    if comment_count > 20:
        content = u'<p>你很厉害<br>' + header \
                  + u'<br>(由于新评论数过多，请登录 %s 查看详情~.~)</p>' % duoshuo_url
        return content
    content = ['<p>' + header + '<br></p>', ]
    for index, meta in enumerate(metas):
        thread_key = meta['thread_key']  # 备份原始 thread_key，用于合成你的文章网址
        meta['created_at'] = meta['created_at'].replace('T', ' ').replace('+08:00', '')
        meta['thread_key'] = get_article_title(meta)
        if comment_count == 1:
            order = ''
        else:
            order = u'第%d条新评论：<br>' % (index + 1)
        meta['message'] = meta['message'].replace(r'\/', r'/').replace(r'\"', r'"')
        comment_info = template['comment_info'] % meta
        click = u'<br>点击查看：{0}{1}<br>'.format(config['myself_author_url'], unicode(thread_key))
        comment = '<p>' + order + '<br>'.join(line.strip() for line in comment_info.splitlines()) + click + '</p>'
        content.append(comment)
    return ''.join(content)

def handler():
    log_url = template['log_url'] % config
    duoshuo_log = get_duoshuo_log(log_url)
    if not duoshuo_log:
        return
    data, last_counter, counter = duoshuo_log
    metas = []
    myself_author_id = config['myself_author_id']
    for i in xrange(counter - last_counter):
        if data['response'][i]['action'] == 'create' and data['response'][i]['meta']['author_id'] != myself_author_id:
            metas.append(data['response'][i]['meta'])
    if not metas:
        return
    comment_count = len(metas)
    content = email_content(comment_count, metas)
    return content
```
  进一步判断产生的新的操作动态的 `action` 是否是 `create` ，以及是否是自己回复别人或者删除评论引起的操作动态的变化。如果条件成立，就意味着有新的评论（是件儿高兴事儿，哈哈）。如果新的评论数超过20条，就不显示详细信息。为了在邮件中显示评论中包含的表情和网址，我以 html 的形式发送邮件。

* **生成message，发送邮件**
```python
def format_email_header(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

def generate_email_msg(content, message_type=None):
    now = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M')
    if message_type == 'comment':
        me_header = u'多说评论提醒'
        sub = u'新评论提醒{0}'
        _subtype = 'html'
        content = '<html><body>' + content + '</body></html>'
    else:
        me_header = u'Comment notifier日志'
        sub = u'脚本出现错误{0}'
        _subtype = 'plain'
    me = me_header + '<' + config['from_address'] + '>'
    msg = MIMEText(content, _subtype=_subtype, _charset='utf-8')
    msg['Subject'] = Header(sub.format(now), 'utf-8').encode()
    msg['From'] = format_email_header(me)
    msg['To'] = config['to_address']
    return msg

def send_email(content, message_type=None):
    msg = generate_email_msg(content, message_type)
    try:
        server = smtplib.SMTP(timeout=10)
        server.connect(config['email_host'])
        server.login(config['from_address'], config['email_password'])
        server.sendmail(config['from_address'], config['to_address'], msg.as_string())
        logger.debug(u'邮件发送成功')
        server.quit()
    except Exception as e:
        logger.exception(e)
```
  由于此脚本需要发送两类邮件，一类是新评论的提醒邮件，一类是脚本运行失败的日志邮件，所以设置了 `message_type` 参数。如果你想使用带有中文的发件人发送邮件，那么 `format_email_header` 函数是需要的。因为如果包含中文，需要通过 `Header` 对象进行编码。如果是新评论的提醒邮件，那么发送 html 形式的邮件；如果是日志邮件，则发送纯文本格式的邮件。

* **监控器**
```python
def monitor():
    logger.debug(u'脚本开始运行...')
    get_config()
    period_of_check = int(config['period']) if platform.system().lower() == "windows" else -1
    while 1:
        content = handler()
        if content:
            send_email(content, message_type='comment')
        else:
            logger.debug(u'暂时还没有新评论')
        if period_of_check > 0:
            logger.debug(u'正在等待({0}s)下一次检查...'.format(period_of_check))
            time.sleep(period_of_check)
        else:
            break
```
  如果你运行这个脚本的系统是 Linux，那么运行一次就结束，因为使用的是 crontab 设置的定时任务，就没有必要 time.sleep(x)了。如果是 Windows系统，就一直运行这个脚本，并间隔一定的周期检查是否有新的评论。