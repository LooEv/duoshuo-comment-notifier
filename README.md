## 介绍
如果你的博客使用了多说评论，那么很不幸，你的博客有了新留言你收不到提醒。多说评论系统设定的是只有别人回复了你的留言才会邮件通知你。虽然刚开始写博客的时候，给我们留言的人很少，或者也许以后也没有多少留言（**此处应该有一个笑哭的表情**，此刻看看窗外，那只猫也在嘲笑我），不过如果有人给我们留言了，那我们及时回复他也是一种尊重他的表现，所以用 python 编写了一个脚本解决多说评论的不完美提醒。
## Requirement
* **python 2.7** 以及 **python 3** 都可运行；
* 此脚本只用到 `requests` 这一个第三方库，请安装：
```bash
$ pip install requests
```

## 实现原理
这是获取 [多说评论后台操作日志](http://dev.duoshuo.com/docs/50037b11b66af78d0c000009) 的官方说明。通过 `requests` 获取博客的评论日志，判断是否产生了新的日志，然后进一步判断是否是别人的评论或者回复（因为你自己回复别人也会产生操作日志），如果条件成立，则发送邮件；否则，等待下一次 check。另外，如果在脚本运行过程中出现问题，脚本会将错误信息以邮件的形式发送给我们，以便我们及时处理。

## 注意事项
请确保你开启了多说评论的通知提醒（在“个人资料”选项中填写邮箱地址），并且选择**每条新回复都提醒我**。因为只有这样设置，你在其他人的博客中留了言，然后别人回复了你，或者在你自己的博客中，别人回复了你，才能收到多说官方的邮件提醒。
而我编写的这个脚本，也是用于你自己博客中留言的邮件提醒。在你自己的博客中，如果别人回复了你（注意区分概念，是回复了你的某一条评论），多说评论官方会发送邮件提醒，此时，脚本就应该判断这条回复的父评论的作者是否是自己，如果是脚本就不发送提醒邮件，以免重复提醒。
![设置多说](http://ocf3ikxr2.bkt.clouddn.com/python/duoshuo_settings.jpg)

## 结果展示
1. 如果新评论数 <= 20，那么显示详细的评论信息，并将文章题目设置为超链接，可以点击访问该文章，效果如下：
![效果展示1](http://ocf3ikxr2.bkt.clouddn.com/python/duoshuo_comment1.jpg)

2. 如果新评论数 > 20，就只是提示功能（显示过多反而不好），如下：
![效果展示2](http://ocf3ikxr2.bkt.clouddn.com/python/duoshuo_comment2.jpg)

3. 正如下面图片中展示的一样，脚本运行发生错误，邮件提示我“获取多说评论后台日志失败”，果然我检测多说网，那天晚上真的宕机了，不过第二天又恢复正常了~.~
![效果展示3](http://ocf3ikxr2.bkt.clouddn.com/python/duoshuo_comment3.jpg)

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
```
请认真仔细填写配置文件。

## 使用方法
**第一步**：
```bash
$ git clone https://github.com/LooEv/duoshuo-comment-notifier.git ~/duoshuo-comment-notifier

$ chmod +x ~/duoshuo-comment-notifier/comment_notifier.py	#这一步很重要！
```

**第二步，编辑 `_config.conf` 文件，将自己的配置信息填写完整。**

**第三步，设置定时运行脚本**：
在 Linux中，运行下面的命令：
```bash
$ crontab -e	# 编辑当前用户的crontab文件
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
恩，那什么，如果你没有 vps,使用的是 Windows 系统，可以使用创建**计划任务**的方式运行脚本，这里就不涉及相关教程了，如有需要请自行 google。

## 让脚本更加友好
为了让脚本的功能更加人性化，我设置了如下的特性：
* 如果新评论数大于20条，就不显示评论的详细信息，只提示评论数，并提示你登录多说网查看详情，因为如果信息过多的话也不方便在邮件里面阅读。
* 如果脚本运行失败的时候又正好有新的评论，需要将 last_counter 重新写入 action_counter_file 中，以免错过新评论。
* 当脚本由于某些原因运行失败，比如无法获取多说网的数据，如果连续运行失败的次数 <= 2，就发送提醒邮件，提醒你检查原因；如果连续运行失败的次数 > 2，就不再发送邮件，因为如果我们暂时不方便修复脚本，提醒邮件就会一直发，让人心烦，所以需要设置这个判断功能。
* 如果脚本连续运行失败的次数过多，而只会发送两封提醒邮件，如果你太忙很容易忘记这件事儿。为了不让你忘记检查原因，就每隔一定时间重新发送提醒邮件给你，发送邮件的周期请自行修改，因为这个周期需要根据你设置的执行脚本的间隔周期调整，才能起到既提醒了你又不扰人的效果。
* 如果脚本运行的日志文件过大，会发送邮件提醒你删除日志（这种情况应该很少会出现，不过以防万一）。

## 实现细节
### 兼容python2和3
```python
try:
    from ConfigParser import ConfigParser  # python2
except ImportError:
    from configparser import ConfigParser  # python3

try:
    from urllib.parse import quote  # python3
except ImportError:
    from urllib import quote  # python2

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
file_of_mistakes = dir_name + os.sep + 'mistakes.log'
the_number_of_mistakes = 0
duoshuo_url = 'http://duoshuo.com/'
```
action_counter_file 文件里面有两个记录，一个是上一次检测你的评论操作数，另一个是上一次检测的时间，以便你确定脚本是否运行过，我之前就忘记给 `comment_notifier.py` 文件添加可执行的权限，导致定时任务运行失败，很久才找到原因，有了时间记录就能表示脚本是否被执行过。 file_of_mistakes 用于记录脚本连续运行失败的次数，如果中途脚本运行成功，就重新置零。

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
            if the_number_of_mistakes == -2:
                with open(file_of_mistakes, 'w') as f:
                    f.write('mistakes:0')
            else:
                if content and (the_number_of_mistakes < 2):
                    # 如果连续运行失败的次数大于两次，就不再发生提醒邮件，如果一直发太影响心情了
                    send_email(u'第{0}次运行出错\n'.format(the_number_of_mistakes + 1) + '\n\n'.join(content))

                elif content and (the_number_of_mistakes > 0) and (the_number_of_mistakes % 50 == 0):
                    # 如果连续运行失败的次数为50的倍数，即每50次运行失败就发送邮件提醒你修复脚本
                    # 如果你设置的定时任务间隔大，比如1天运行一次，请自行修改上面的判断条件，以便你及时修复脚本
                    send_email(u'多说评论邮件提醒脚本已经第{0}次运行失败了，请尽快查找原因！'.format(the_number_of_mistakes))

                if content:
                    with open(file_of_mistakes, 'w') as f:
                        f.write('mistakes:' + str(the_number_of_mistakes + 1))
            self.release()
            del content

def set_logger():
    get_the_number_of_mistakes()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    log_name = (dir_name + os.sep + 'notifier.log')
    fh = logging.FileHandler(filename=log_name)
    if the_number_of_mistakes <= 1:
        fh.setLevel(logging.ERROR)
    else:
        # 防止导致脚本运行失败的错误的详细信息反复写入日志，只需写入简要的错误说明即可，控制日志文件的大小
        fh.setLevel(logging.CRITICAL)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(lineno)-3d - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    log_send = BufferingSMTPHandler(10)
    log_send.setLevel(logging.CRITICAL)
    logger.addHandler(log_send)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
```
  为了方便调试，我设置了日志器，此日志器既可以在标准输出流中输出，也可以将 ERROR 级别的日志记录在 notifier.log 文件中，还可以通过邮件发送 CRITICAL 级别的日志，`BufferingSMTPHandler` 是我以 `logging.handlers.BufferingHandler` 创建的子类。当然也可以使用 `logging.handlers.SMTPHandler`， 不过会出现一个问题，就是有几条 CRITICAL 级别的日志，它就会给你发送几封邮件，这是我们不想要的结果，我们需要的是汇总邮件，一封就够。定义 `BufferingSMTPHandler` 的好处是如果因为某些原因导致脚本运行失败我们能够及时知道并处理。如果有不明白的地方，建议看 [logging.handlers](https://hg.python.org/cpython/file/2.7/Lib/logging/handlers.py) 的源码。

* **获取多说评论后台日志**
```python
def get_duoshuo_log(url):
    first = False
    if os.path.isfile(action_counter_file):
        with open(action_counter_file) as f:
            last_counter = int(f.read().splitlines()[0])
    else:
        logger.debug(u'没有找到action_counter.log文件，我假设你博客的留言你已经全部看过，也就是没有新留言！')
        last_counter = 0
        first = True
    counter = ''
    try:
        my_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/51.0.2704.103 Safari/537.36',
            'Accept-Encoding': 'gzip'}
        req = requests.get(url, headers=my_headers, timeout=10)
    except Exception as e:
        logger.exception(e)
        logger.critical(u'获取多说评论后台日志失败！')
        raise
    else:
        data = req.json()
        if data['code'] == 0:
            logger.debug(u'获取多说评论后台操作日志成功')
            counter = len(data['response'])
            if counter == 0 or first or last_counter == 0:
                return
            if last_counter != counter:
                return data, last_counter, counter
    finally:
        with open(action_counter_file, 'w') as f:
            f.write(str(counter) if counter else str(last_counter))
            f.write('\nlast checked time: ' + time.ctime())
```
  action_counter_file 文件是记录上一次运行脚本检查到的你的多说评论后台有多少个评论操作数，包括别人给你的评论和回复，你给别人的回复，以及你删除评论的操作总次数。通过判断日志操作数是否发生变化得知是否有新的操作动态。

* **处理评论日志并生成邮件内容**
```python
def get_title_and_parent_comment(meta):
    first = True
    max_pages = 1
    article_title = unicode(meta['thread_key'])
    parent_comment = ''
    parent_author_name = ''
    recursion = 2 if (not meta['parent_id']) else 50
    myself_author_id = config['myself_author_id']
    try:
        for page in xrange(1, recursion):
            if page > max_pages:
                break
            article_info_url = template['article_info_url'] % (meta['thread_id'], config['short_name'], page)
            req = requests.get(article_info_url, timeout=10)
            data = req.json()
            if data['code'] == 0:
                if first:
                    article_title = unicode(data['thread']['title'])
                    max_pages = data['cursor']['pages']
                    first = False
                if recursion > 2:
                    try:
                        author_id = data['parentPosts'][meta['parent_id']]['author_id']
                        if author_id == myself_author_id:
                            return
                        else:
                            parent_author_name = unicode(data['parentPosts'][meta['parent_id']]['author']['name'])
                            parent_comment = unicode(data['parentPosts'][meta['parent_id']]['message'])
                    except:
                        continue
        return article_title, parent_comment, parent_author_name
    except Exception as e:
        logger.exception(e)
        logger.critical(u'获取文章题目、父评论失败')

def email_content(comment_count, metas):
    header = u'你有{0}条新评论'.format(comment_count)
    log_msg = u'{0}，正在生成邮件内容'.format(header)
    logger.debug(log_msg)
    if comment_count > 20:
        content = u'<p>你的博客很热闹<br>{0}<br>(由于新评论数过多，请登录 {1} 查看详情~.~)</p>'.format(header, duoshuo_url)
        return content
    content = ['<p>' + header + '<br><br></p>', ]
    for index, meta in enumerate(metas):
        thread_key = quote(meta['thread_key'], safe=':+-/')  # 备份原始 thread_key，用于合成你的文章网址
        meta['created_at'] = meta['created_at'].replace('T', ' ').replace('+08:00', '')
        meta['article_url'] = config['myself_author_url'] + unicode(thread_key)
        if not meta['author_url']:
            meta['author_url'] = u'无'
        if comment_count == 1:
            order = ''
        else:
            order = u'第{0}条新评论：<br>'.format(index + 1)
        meta['message'] = meta['message'].replace(r'\/', r'/').replace(r'\"', r'"')
        if not meta['parent_comment']:
            comment_info = template['comment_info_1'] % meta
        else:
            comment_info = template['comment_info_2'] % meta
        comment = '<p>' + order + '<br>'.join(line.strip() for line in comment_info.splitlines()) + '<br><br></p>'
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
            title_parent_comment = get_title_and_parent_comment(data['response'][i]['meta'])
            if not title_parent_comment:
                continue
            else:
                data['response'][i]['meta']['article_title'] = title_parent_comment[0]
                data['response'][i]['meta']['parent_comment'] = title_parent_comment[1]  # 父评论有可能是 ''
                data['response'][i]['meta']['parent_author_name'] = title_parent_comment[2]  # 父评论的作者昵称有可能是 ''
                metas.append(data['response'][i]['meta'])
    if not metas:
        return
    comment_count = len(metas)
    content = email_content(comment_count, metas)
    return content
```
  进一步判断产生的新的操作动态的 `action` 是否是 `create` ，以及是否是自己回复别人或者删除评论引起的操作动态的变化。如果条件成立，就意味着有新的评论（是件儿高兴事儿，哈哈）。接着判断新评论是否有父评论，如果有则获取父评论的内容以及作者，将其显示在邮件中。 如果新的评论数超过20条，就不显示详细信息。为了在邮件中显示评论中包含的表情和网址，我以 html 的形式发送邮件并使用 `quote` 编码网址。

* **生成message，发送邮件**
```python
def format_email_header(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

def generate_email_msg(content, message_type=None):
    now = time.strftime('%Y-%m-%d %H:%M', time.localtime())
    file_size_warning = ''
    if os.path.isfile(log_file):
        if (os.path.getsize(log_file) / 1024.0 / 1024.0) > 200:
            file_size_warning = u'温馨提示：脚本日志文件过大，建议删除。'
    if message_type == 'comment':
        me_header = u'多说评论提醒'
        sub = u'新评论提醒{0}'
        _subtype = 'html'
        content = u'<html><body>{0}<p>{1}</p></body></html>'.format(content, file_size_warning)
    else:
        # when message_type is 'log'
        me_header = u'Comment notifier日志'
        sub = u'脚本出现错误{0}'
        _subtype = 'plain'
        content = content + '\n' + file_size_warning
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
        logger.debug(u'{0}邮件发送成功'.format(u'评论提醒' if message_type == 'comment' else u'日志提醒'))
        server.quit()
    except Exception as e:
        logger.exception(e)
        logger.error(u'邮件发送失败！')
```
  由于此脚本需要发送两类邮件，一类是新评论的提醒邮件，一类是脚本运行失败的日志邮件，所以设置了 `message_type` 参数。如果你想使用带有中文的发件人发送邮件，那么 `format_email_header` 函数是需要的。因为如果包含中文，需要通过 `Header` 对象进行编码。如果是新评论的提醒邮件，那么发送 html 形式的邮件；如果是日志邮件，则发送纯文本格式的邮件。如果脚本日志文件过大，就在发送邮件的时候附带温馨提醒。

* **监控器**
```python
def monitor():
    logger.debug(u'脚本开始运行...')
    get_config()
    try:
        content = handler()
        if content:
            send_email(content, message_type='comment')
    except Exception as e:
        logger.exception(e)
    else:
        global the_number_of_mistakes
        the_number_of_mistakes = -2
        if not content:
            logger.debug(u'暂时还没有新评论')
    finally:
        # 如果脚本出现问题，确保日志会通过邮件发送给你
        logging.shutdown()
```
  调用相关函数，开始检测。