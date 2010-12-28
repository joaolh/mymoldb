#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     functions.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  100428

'''basic functions for the site'''
import web, sys, os, hashlib, re, smtplib, MySQLdb as mysql

def autoreload(module_list, modules = sys.modules):
    for mod_name in module_list:
        try:
            module = modules[mod_name]
        except:
            continue
        mtime = os.path.getmtime(module.__file__)
        try:
            if mtime > module.loadtime:
                reload(module)
        except:
            pass
        module.loadtime = mtime

class trans():
    def __init__(self, dic_file_path):
        self.lang = 'zh_CN'
        self.dic_file_path = ( lambda x: x.endswith('/') and x or x + '/' ) ( dic_file_path )
        self.dic = {}
        for f in os.listdir(self.dic_file_path):
            lang = ''
            if f.endswith('.txt'):
                lang = f.rstrip('.txt')
                tmpl = []
                tmpdic = {}
                try:
                    for w in open((self.dic_file_path + f)):
                        if not w.startswith('#') and len(w) > 1:
                            tmpl = w.split(':', 1)
                            tmpdic[tmpl[0]] = tmpl[1].rstrip('\n')
                except:
                    pass
                if lang:
                    self.dic[lang] = tmpdic
    def trans(self, words):
        '''translate the words according to dic'''
        dic = self.dic[self.lang]
        words = str(words)
        if dic.has_key(words):
            return dic[words]
        else:
            return words
    def selected(self, lang):
        if lang == self.lang:
            return "selected"

def is_selected(arg):
    return lambda x: x == arg and "selected" or ""

def md5(string):
    if string:
        m = hashlib.md5()
        m.update(string)
        return m.hexdigest()
    return ""

def query_preprocessing(query):
    '''preprocessing the query to prevent sql injection'''
    black_words = ['select', 'insert', 'update', 'drop', 'source', 'join']
    black_symbals = [';']
    def gen_re_string(string):
        s = '\\s'
        for i in str(string):
            s += '[' + i + i.upper() + ']'
        s += '\\s'
        return s
    for i in black_words:
        if re.findall(gen_re_string(i), query):
            raise Exception, "query contains illegal word '" + i + "'"
    for i in black_symbals:
        if re.findall(i, query):
            raise Exception, "query contains illegal symbal '" + i + "'"
    return mysql.escape_string(query)

def permission_check(
        user,
        user_group,
        actions = ('s',),
        involved_user = None,
        actions_rules = None):
    action_match = True
    # actions check
    actions_rule = actions_rules[user_group]
    for a in actions:
        if not (a in actions_rule):
            action_match = False
            break
    if action_match:
        return True
    elif user == involved_user:
        return True
    else:
        return False

def sendmail(settings, to_addr, subject = '', msg = ''):
    try:
        smtp = settings['smtp']
        from_addr = settings['from']
        user = settings['user']
        passwd = settings['passwd']
    except:
        return 'settings not perfection'
    msg = 'To: ' + to_addr + '\r\nFrom: ' + from_addr + '\r\nSubject: ' + subject + '\r\n\r\n' + msg
    s = smtplib.SMTP(smtp)
    login_stat = s.login(user, passwd)
    if login_stat[0] == 235:
        send_stat = s.sendmail(from_addr, to_addr, msg)
        if not send_stat:
            return 0
    else:
        return 1

if __name__ == '__main__':
    q = "niha' &kdjfgi||[] and = %^^$#@ _insert*"
    print query_preprocessing(q)
    t = trans('en_US').trans
    print t('welcome here')
