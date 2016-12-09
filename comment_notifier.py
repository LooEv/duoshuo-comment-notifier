#!/usr/bin/env python
# encoding: utf-8
# Author: LooEv


import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, parseaddr

try:
    from ConfigParser import ConfigParser  # python2
except ImportError:
    from configparser import ConfigParser  # python3

try:
    from urllib.parse import quote  # python3
except ImportError:
    from urllib import quote  # python2

import requests
import logging, logging.handlers
import time
import sys
import os

if sys.version_info[0] >= 3:
    unicode = str
    xrange = range

config = {}
dir_name = os.path.dirname(os.path.abspath(__file__))
config_file = dir_name + os.sep + '_config.conf'
action_counter_file = dir_name + os.sep + 'action_counter.log'
file_of_mistakes = dir_name + os.sep + 'mistakes.log'
the_number_of_mistakes = 0
log_file = dir_name + os.sep + 'notifier.log'
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
                    s = u'多说评论邮件提醒脚本已经第{0}次运行失败了，请尽快查找原因！\n'.format(the_number_of_mistakes)
                    send_email(s + '\n\n'.join(content))

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
    fh = logging.FileHandler(filename=log_file)
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


def get_config():
    conf = ConfigParser()
    try:
        conf.read(config_file)  # 请将配置文件放在当前目录下
        sections = ['duoshuo_account', 'email_info']
        for section in sections:
            for key, value in conf.items(section):
                config[key] = value
    except Exception as e:
        logger.exception(e)
        logger.error(u'读取配置文件失败！！！请正确配置，否则无法发送邮件。')
        sys.exit(1)
    logger.debug(u'读取配置文件')


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
            f.write('\nlast checked time: {0}'.format(time.ctime()))


def get_article_title(meta):
    article_info_url = template['article_info_url'] % (unicode(meta['thread_key']), config['short_name'])
    try:
        req = requests.get(article_info_url, timeout=10)
        data = req.json()
        if data['code'] == 0:
            article_title = data['thread']['title']
            return unicode(article_title)
        else:
            return unicode(meta['thread_key'])
    except Exception as e:
        logger.exception(e)


def email_content(comment_count, metas):
    header = u'你有{0}条新评论'.format(comment_count)
    log_msg = header + u'，正在生成邮件内容'
    logger.debug(log_msg)
    if comment_count > 20:
        content = u'<p>你很厉害<br>{0}<br>(由于新评论数过多，请登录 {1} 查看详情~.~)</p>'.format(header, duoshuo_url)
        return content
    content = ['<p>' + header + '<br></p>', ]
    for index, meta in enumerate(metas):
        thread_key = quote(meta['thread_key'], safe=':+-/')  # 备份原始 thread_key，用于合成你的文章网址
        meta['created_at'] = meta['created_at'].replace('T', ' ').replace('+08:00', '')
        meta['thread_key'] = get_article_title(meta)
        if comment_count == 1:
            order = ''
        else:
            order = u'第{0}条新评论：<br>'.format(index + 1)
        meta['message'] = meta['message'].replace(r'\/', r'/').replace(r'\"', r'"')
        comment_info = template['comment_info'] % meta
        click = u'<br>点击查看：{0}{1}<br>'.format(config['myself_author_url'], unicode(thread_key))
        comment = '<p>' + order + '<br>'.join(line.strip() for line in comment_info.splitlines()) + click + '</p>'
        content.append(comment)
    return ''.join(content)


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


def get_the_number_of_mistakes():
    global the_number_of_mistakes
    if os.path.isfile(file_of_mistakes):
        with open(file_of_mistakes) as f:
            the_number_of_mistakes = int(f.read().split(':')[1])


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


if __name__ == '__main__':
    logger = set_logger()
    monitor()
