#!/usr/bin/env python
# encoding: utf-8
# Author: LooEv

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, parseaddr
from datetime import datetime

try:
    from ConfigParser import ConfigParser
except:
    from configparser import ConfigParser

import requests
import logging, logging.handlers
import platform
import time
import os

config = {}
dir_name = os.path.dirname(os.path.abspath(__file__))
config_file = dir_name + os.sep + '_config.conf'
action_counter_file = dir_name + os.sep + 'action_counter.log'

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


# 如果你修改脚本之后运行没有问题了，请修改日志级别，以防日志文件过大
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


def get_config():
    conf = ConfigParser()
    try:
        conf.read(config_file)  # 请将配置文件放在当前目录下
    except IOError as e:
        logger.exception(e)
    sections = ['duoshuo_account', 'email_info', 'period_of_check']
    for section in sections:
        for key, value in conf.items(section):
            config[key] = value
    logger.debug(u'读取配置文件')


def format_email_header(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr.encode('utf-8') if isinstance(addr, unicode) else addr))


def generate_message(content, message_type=None):
    now = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M')
    if message_type == 'comment':
        me_header = u'多说评论提醒'
        sub = u'新评论提醒{0}'
    else:
        # when message_type is 'log'
        me_header = u'Comment notifier日志'
        sub = u'脚本出现错误{0}'
    me = me_header + '<' + config['from_address'] + '>'
    msg = MIMEText(content, _subtype='plain', _charset='utf-8')
    msg['Subject'] = Header(sub.format(now), 'utf-8').encode()
    msg['From'] = format_email_header(me)
    msg['To'] = config['to_address']
    return msg


def send_email(content, message_type=None):
    msg = generate_message(content, message_type)
    try:
        server = smtplib.SMTP(timeout=10)
        server.connect(config['email_host'])
        server.login(config['from_address'], config['email_password'])
        server.sendmail(config['from_address'], config['to_address'], msg.as_string())
        logger.debug(u'邮件发送成功')
        server.quit()
    except Exception as e:
        logger.exception(e)


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


def get_article_title(meta):
    article_info_url = template['article_info_url'] % (meta['thread_key'], config['short_name'])
    try:
        req = requests.get(article_info_url, timeout=10)
        data = req.json()
        if data['code'] == 0:
            article_title = data['thread']['title']
            return unicode(article_title)
        else:
            return meta['thread_key']
    except Exception as e:
        logger.exception(e)


def email_content(comment_count, metas):
    header = u'你有%d条新评论' % comment_count
    log_msg = header + u'，正在生成邮件内容'
    logger.debug(log_msg)
    if comment_count > 20:
        duoshuo_url = 'http://duoshuo.com/'
        content = u'你很厉害\n' + header \
                  + u'(由于新评论数过多，请登录 %s 查看详情~.~)' % duoshuo_url
        return content
    content = [header + u'\n', ]
    for index, meta in enumerate(metas):
        meta['created_at'] = meta['created_at'].replace('T', ' ').replace('+08:00', '')
        meta['thread_key'] = get_article_title(meta)
        order = u'第%d条新评论：\n' % (index + 1)
        comment_info = template['comment_info'] % meta
        click = u'\n点击查看：{0}{1}\n'.format(config['myself_author_url'], unicode(meta.get('thread_key')))
        comment = order + '\n'.join(line.strip() for line in comment_info.splitlines()) + click
        content.append(comment)
    return '\n'.join(content)


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


def monitor():
    logger.debug(u'脚本开始运行...')
    get_config()

    # 如有需要，请自行修改此处代码
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


if __name__ == '__main__':
    try:
        logger = set_logger()
        monitor()
    finally:
        # 如果脚本出现问题，确保日志会通过邮件发送给你
        logging.shutdown()
