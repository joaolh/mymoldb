#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     main.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  091216

import web, sys, os, hashlib, zlib, re, time, pickle, base64, json
from settings import *
import libmymoldb as lm
from libmymoldb.functions import *
reload(sys)
sys.setdefaultencoding('utf-8')

# =====================================================BEGIN INITIALIZATION==============================================

# init the permission check function
is_permited = lambda user, user_group, actions = ('s',), involved_user = None, actions_rules = None: \
        permission_check(user, user_group, actions, involved_user, ACTIONS_RULES)

# init the web application
app = web.application(URL_MAP, globals())

# init session
session = SESSION(app)

# init class for translation
trans_class = trans(dic_file_path = TRANS_PATH)

# init dbdef object
dbd_objs = {}
for i in DATABASES:
    dbd_objs[i] = lm.dbdef(ENVS[i]['DEF_FILE'])

# results dic template
tpl_results_dic = {
        'links': NAV_LINKS,
        'logged_user': None,
        'result_list': [],
        'len_results': 0,
        'dbs': PUBLIC_DBS,
        'db': '1',
        'mol': '',
        'table_heads': [],
        'max_results_num': 300,
        'pages': 1,
        'page': 1,
        'search_mol': '',
        'trans_class': None,
        'db_selected': is_selected('1'),
        'mode_selected': is_selected('2'),
        'query_id': '',
        'time_consumed': 0,
        'last_query_id': '',
        'last_db': '',
        'adv_search_query': '',
        'results_search_type': '2',
        'query_mols_dic': {},
        'lang': 'zh_CN',
        'html_title': '',
        'info_head': 'info',
        'info': [],
        'min_simi': '0',
        'urls_dic': URLS_DIC,
        'current_page': ''
        }

# make html pages from templates
html_normal_search = lambda results: WEB_RENDER('header', results_dic = results) + \
        WEB_RENDER('normal_editor', results_dic = results) +\
        WEB_RENDER('last_query', results_dic = results) + \
        WEB_RENDER('display_results', results_dic = results) + \
        WEB_RENDER('footer', results_dic = results)
html_advanced_search = lambda results: WEB_RENDER('header', results_dic = results) + \
        WEB_RENDER('advanced_editor', results_dic = results) +\
        WEB_RENDER('last_query', results_dic = results) + \
        WEB_RENDER('display_results', results_dic = results) + \
        WEB_RENDER('footer', results_dic = results)
html_molinfo = lambda results: WEB_RENDER('header', results_dic = results) + \
        WEB_RENDER('molinfo', results_dic = results) +\
        WEB_RENDER('footer', results_dic = results)
html_info = lambda results: WEB_RENDER('header', results_dic = results) + \
        WEB_RENDER('info', results_dic = results) +\
        WEB_RENDER('footer', results_dic = results)
html_index = lambda results: WEB_RENDER('header', results_dic = results) + \
        WEB_RENDER('index', results_dic = results) +\
        WEB_RENDER('footer', results_dic = results)
html_login = lambda results: WEB_RENDER('header', results_dic = results) + \
        WEB_RENDER('login', results_dic = results) +\
        WEB_RENDER('footer', results_dic = results)
html_register = lambda results: WEB_RENDER('header', results_dic = results) + \
        WEB_RENDER('register', results_dic = results) +\
        WEB_RENDER('footer', results_dic = results)
html_edit = lambda results: WEB_RENDER('header', results_dic = results) + \
        WEB_RENDER('edit', results_dic = results) +\
        WEB_RENDER('footer', results_dic = results)
html_ucpanel = lambda results: WEB_RENDER('header', results_dic = results) + \
        WEB_RENDER('ucpanel', results_dic = results) +\
        WEB_RENDER('footer', results_dic = results)

def html_no_permision(results_dic):
    results_dic['html_title'] = 'permission denied'
    results_dic['info'].append('you have no permission to access here')
    return html_info(results_dic)
def html_query_imcomplete(results_dic):
    results_dic['info'].append('query imcomplete')
    results_dic['html_title'] = 'query err'
    return html_info(results_dic)
def html_query_illegal(results_dic):
    results_dic['info'].append('contains illegal words')
    results_dic['html_title'] = 'query err'
    return html_info(results_dic)
def html_wrong_db(results_dic):
    results_dic['info'].append('wrong db name')
    results_dic['html_title'] = 'wrong db name'
    return html_info(results_dic)

#================================================END INITIALIZATION==============================================

#=======================================================MAIN=====================================================

# The main script of the web site mymoldb

# web site classes
class index:
    def __init__(self):
        # set the target language to session.lang
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'mode_selected': is_selected(str(session.search_mode)),
            'html_title': 'home',
            'info': [],
            'current_page': 'home',
            'lang': session.lang
            } )
    def GET(self, name = ''):
        results_dic = self.results_dic
        return html_info(results_dic)

class register:
    def __init__(self):
        # set the target language to session.lang
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'mode_selected': is_selected(str(session.search_mode)),
            'html_title': 'register',
            'ref': URLS_DIC["home_url"],
            'info': [],
            'lang': session.lang
            } )
    def GET(self, name = ''):
        if not session.authorized:
            return html_register(self.results_dic)
        else:
            web.seeother(self.results_dic['ref'])
    def POST(self, name = ''):
        input = web.input()
        results_dic = self.results_dic

        for i in ('nick', 'passwd', 'cfm_pw', 'username'):
            if not ( input.has_key(i) and input.get(i) ):
                results_dic['info'].append('info not complete')
                return html_register(results_dic)

        nick = query_preprocessing(input.get('nick'))
        if not 2 <= len(nick) <= 20:
            results_dic['info'].append('nick length not fit')
            return html_register(results_dic)

        # username is email
        username = query_preprocessing(input.get('username'))
        if not re.match(r'[._0-9a-zA-Z]+@[._0-9a-zA-Z]+', username):
            results_dic['info'].append('not valid username')
            return html_register(results_dic)

        # passwd is about to hash, so, no need to preprocess
        passwd = input.get('passwd')
        if passwd != input.get('cfm_pw'):
            results_dic['info'].append('pass word not well confirmed')
            return html_register(results_dic)

        # check if the username available
        env_db = ENVS[USERSDB]
        userdb_obj = lm.users_db(env_db)
        if userdb_obj.select(['*'], '%s = "%s"' %(env_db['USER_EMAIL_FIELD'], username)):
            results_dic['info'] += ['user already registered', ': ', username]
            userdb_obj.close()
            return html_register(results_dic)
        userdb_obj.close()

        if APPROVE_ALL_REGISTERS:
            # to add auto register
            userdb_obj = lm.users_db(env_db)
            userdb_obj.insert_into_usersdb('', nick, DEFAULT_USER_GROUP, md5(passwd), username, time.strftime('%Y-%m-%d %H:%M:%S'), 1)
            results_dic['info'] += ['register finished', 'you can login now']
            userdb_obj.close()
        else:
            tmp_info_dic = {'username': username, 'group': DEFAULT_USER_GROUP, 'nick': nick, 'passwd': md5(passwd)}
            id = md5(str(tmp_info_dic))
            info_dic = { id: tmp_info_dic }
            try:
                register_info_file = open(REGISTER_INFO_FILE, 'r')
                info_dic_from_file = pickle.load(register_info_file)
                register_info_file.close()
                if not info_dic_from_file.has_key(id):
                    info_dic_from_file.update(info_dic)
                else:
                    results_dic['info'] += ['you hava already submited your info', ',', 'please waiting for been approved']
                    return html_register(results_dic)
                register_info_file = open(REGISTER_INFO_FILE, 'w')
                pickle.dump(info_dic_from_file, register_info_file)
                register_info_file.close()
            except:
                register_info_file = open(REGISTER_INFO_FILE, 'w')
                pickle.dump(info_dic, register_info_file)
                register_info_file.close()

            results_dic['info'] += ['register finished', ',', 'please waiting for been approved']
        return html_register(results_dic)

class login:
    '''class for user login/logout'''
    def __init__(self):
        # set the target language to session.lang
        trans_class.lang = session.lang
        self.last_login_time = session.last_login_time
        self.login_try_times = session.login_try_times
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'mode_selected': is_selected(str(session.search_mode)),
            'html_title': 'login',
            'ref': URLS_DIC["home_url"],
            'info': [],
            'lang': session.lang
            } )
    def GET(self, name = ''):
        results_dic = self.results_dic
        ref = '/'
        input = web.input()
        if input.has_key('ref') and input.get('ref'):
            if  input.get('ref') != web.ctx.path:
                ref = input.get('ref')

        # logout
        if input.has_key('action') and input.get('action'):
            if input.get('action') == 'logout':
                session.kill()
                return 'logout OK'

        if session.authorized:
            return web.seeother(ref)

        results_dic['ref'] = ref

        if self.login_try_times >= MAX_LOGIN_TRY_TIMES:
            if time.time() - self.last_login_time < LOGIN_INTERVAL:
                results_dic["info"].append('try again after a while')
                return html_info(self.results_dic)
            else:
                session.login_try_times = 0
        else:
            session.login_try_times += 1
        return html_login(results_dic)

    def POST(self, name = ''):
        input = web.input()
        env_db = ENVS[USERSDB]
        userdb_obj = lm.users_db(env_db)
        results_dic = self.results_dic
        ref = '/'

        if input.has_key('ref') and input.get('ref'):
            ref = base64.b64decode(input.get('ref'))
            if  ref != web.ctx.path:
                results_dic['ref'] = ref

        if session.authorized:
            return web.seeother(ref)

        if ( input.has_key("username") and input.get("username") ) \
                and ( input.has_key("password") and input.get("password") ):
            # user password
            pw = ''
            # default user group is 3 (viewer)
            ug = session.usergroup
            # user name
            nm = query_preprocessing(input.get("username"))
            # username should be email
            if not re.match(r'[0-9_.a-zA-Z]+@[0-9_.a-zA-Z]+', nm):
                results_dic['info'].append("not valid user name")
                return html_login(results_dic)

            # try to connect to the user accounts db to verify the login info of the user
            user_info = userdb_obj.select(['*'], '%s = "%s" LIMIT 1' %(env_db['USER_EMAIL_FIELD'], nm))
            if user_info:
                user_info_dic = user_info[0]
                status = user_info_dic.get(env_db['STATUS_FIELD'])
                if status != 1:
                    results_dic['info'].append("user had been deactived")
                    return html_login(results_dic)
                else:
                    pw = user_info_dic.get(env_db['PASSWORD_FIELD'])
                    ug = user_info_dic.get(env_db['USER_GROUP_FIELD'])
                    ui = user_info_dic.get(env_db['USER_ID_FIELD'])
                    nk = user_info_dic.get(env_db['NICK_FIELD'])
                    if pw == md5(input.get("password")):
                        session.authorized = True
                        # if no nick name, then use user name (the email) as nick name
                        if not nk:
                            session.nickname = nm
                        else:
                            session.nickname = nk
                        session.usergroup = ug
                        session.userid = ui
                        session.username = nm
                    else:
                        results_dic['info'].append("pass word incorrect")
                        return html_login(results_dic)
            else:
                results_dic['info'].append("user not valid")
                return html_login(results_dic)
        return web.seeother(ref)

class man_users:
    def __init__(self):
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'lang': session.lang,
            'groups': ', '.join([ str(i) for i in USER_GROUPS ]),
            'info': [],
            'current_page': ''
            } )
    def GET(self, name = ''):
        input = web.input()
        results_dic = self.results_dic
        env_db = ENVS[USERSDB]
        if ( not session.authorized ) or session.usergroup != 1:
            results_dic['info'].append('you have no permission to access here')
            return WEB_RENDER('info', results = results_dic)

        userdb_obj = lm.users_db(env_db)
        # select out the users in group 1 ( administrators ), in case no administrator left
        # after removment or deactivation
        admins = []
        for a in userdb_obj.select([env_db['USER_ID_FIELD']], '%s = "%s"' %(env_db['USER_GROUP_FIELD'], '1')):
            if a.has_key(env_db['USER_ID_FIELD']):
                admins.append(a.get(env_db['USER_ID_FIELD']))

        if input.has_key('approve_id') and input.get('approve_id'):
            try:
                register_info_file = open(REGISTER_INFO_FILE, 'r')
                info_dic_from_file = pickle.load(register_info_file)
                register_info_file.close()
                info = info_dic_from_file.get(input.get('approve_id'))
                # send email to notify user
                sendmail(SENDMAIL_SETTINGS_DICT,
                        info['username'],
                        'MyMolDB register successed notify',
                        '''
Dear %s,

Your application on MyMolDB as a contributor and user has been approved, you can login the site with the user name %s.

The URL of our site is http://xxxxxxxxxx.xxx/db/.

Welcome!

Sincerely yours''' %(info['nick'], info['username']) )

                userdb_obj.insert_into_usersdb('', info['nick'], DEFAULT_USER_GROUP, info['passwd'], info['username'], time.strftime('%Y-%m-%d %H:%M:%S'), 1)
                # delete the info in REGISTER_INFO_FILE after the register procedure finished
                info_dic_from_file.pop(input.get('approve_id'))
                register_info_file = open(REGISTER_INFO_FILE, 'w')
                pickle.dump(info_dic_from_file, register_info_file)
                register_info_file.close()
                results_dic['info'] += ['approve user', info['username'], 'successed']
            except:
                results_dic['info'] += ['approve user', info['username'], 'failed']

        if input.has_key('active_id') and input.get('active_id'):
            active_id = input.get('active_id')
            userdb_obj.update_usersdb(
                    {env_db['STATUS_FIELD']: '1'},
                    '%s = "%s"' %(env_db['USER_ID_FIELD'], active_id) )
            results_dic['info'] += ['active', 'user', active_id, '(id)', 'successed']

        if input.has_key('deactive_id') and input.get('deactive_id'):
            deactive_id = input.get('deactive_id')
            if len(admins) <= 1 and int(deactive_id) in admins:
                results_dic['info'] += ['at least one admin is needed', ', ', 'you can not', 'deactive', 'it']
            else:
                userdb_obj.update_usersdb(
                        {env_db['STATUS_FIELD']: '0'},
                        '%s = "%s"' %(env_db['USER_ID_FIELD'], input.get('deactive_id')) )
                results_dic['info'] += ['deactive', 'user', deactive_id, '(id)', 'successed']

        if input.has_key('remove_id') and input.get('remove_id'):
            remove_id = input.get('remove_id')
            if len(admins) <= 1 and int(remove_id) in admins:
                results_dic['info'] += ['at least one admin is needed', ', ', 'you can not', ' ', 'remove', 'it']
            else:
                userdb_obj.delete('%s = "%s"' %(env_db['USER_ID_FIELD'], input.get('remove_id')))
                results_dic['info'] += ['remove', 'user', remove_id, '(id)', 'successed']

        if ( input.has_key('chgroup_id') and input.get('chgroup_id') ) and \
                ( input.has_key('group') and int(input.get('group')) in USER_GROUPS):
            id = input.get('chgroup_id')
            group = input.get('group')
            userdb_obj.update_usersdb(
                    {env_db['USER_GROUP_FIELD']: group},
                    "%s = '%s'" %(env_db['USER_ID_FIELD'], id) )
            results_dic['info'] += [chgroup_id, '(id)', 'change group', 'to', group, 'successed']

        approved_users = []
        unapproved_users = []
        user_info = userdb_obj.select(['*'], '1')
        userdb_obj.close()

        if user_info:
            for info in user_info:
                approved_users.append(
                        (str(info[env_db['USER_ID_FIELD']]),
                        info[env_db['USER_GROUP_FIELD']],
                        info[env_db['USER_EMAIL_FIELD']],
                        info[env_db['NICK_FIELD']],
                        str(info[env_db['STATUS_FIELD']])) )

        try:
            register_info_file = open(REGISTER_INFO_FILE, 'r')
            info_dic_from_file = pickle.load(register_info_file)
            register_info_file.close()
            for id, info in info_dic_from_file.items():
                # '-1' means still not approved, '0' means inactive while '1' is active
                unapproved_users.append( (id, info['group'], info['username'], info['nick'], '-1') )
        except:
            pass

        results_dic['approved_users'] = approved_users
        results_dic['unapproved_users'] = unapproved_users
        #return approved_users, unapproved_users
        return WEB_RENDER('man_users', results_dic = results_dic)

class ucpanel:
    def __init__(self):
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.userid = session.userid
        self.nickname = session.nickname
        self.usergroup = session.usergroup
        self.results_dic.update( {
            'logged_user': self.nickname,
            'trans_class': trans_class,
            'lang': session.lang,
            'html_title': 'user control panel',
            'ucp_urls': [],
            'info': [],
            'current_page': ''
            } )
    def GET(self, name = ''):
        results_dic = self.results_dic
        if ( not session.authorized ) or ( not is_permited(session.userid, session.usergroup, ('s')) ):
            return html_no_permision(results_dic)
        results_dic['ucp_urls'] += UCP_URLS
        # users in group 1 are administrators, so, show them the user management option
        if session.usergroup == 1:
            user_man_url = ('user management', URLS_DIC['manusers_url'], '')
            if not user_man_url in results_dic['ucp_urls']:
                results_dic['ucp_urls'].append(user_man_url)
        return html_ucpanel(results_dic)

class chusersettings:
    def __init__(self):
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'lang': session.lang,
            'reload_parent': False,
            'info': [],
            'nick_name': session.nickname,
            'email': session.username
            } )
    def GET(self, name = ''):
        # check basic permission
        if ( not session.authorized ) or ( not is_permited(session.userid, session.usergroup, ('s')) ):
            return html_no_permision(self.results_dic)
        return WEB_RENDER('chusersettings', results_dic = self.results_dic)
    def POST(self, name = ''):
        # check basic permission
        if ( not session.authorized ) or ( not is_permited(session.userid, session.usergroup, ('s')) ):
            return html_no_permision(self.results_dic)

        input = web.input()
        results_dic = self.results_dic
        partial_sql = ''
        sql_string = ''
        new_nick = ''
        new_email = ''
        env_db = ENVS[USERSDB]
        old_pw = ''
        quit = False

        if input.has_key('nick') and input.get('nick'):
            new_nick = input.get('nick')
            if new_nick != session.nickname:
                if 2 <= len(new_nick) <= 20:
                    partial_sql += ' %s = "%s", ' %(env_db['NICK_FIELD'], new_nick)

        if ( input.has_key('new_pw') and input.get('new_pw') ) and ( input.has_key('cfm_pw') and input.get('cfm_pw') ):
            new_pw = input.get('new_pw')
            if new_pw == input.get('cfm_pw'):
                if input.has_key('old_pw') and input.get('old_pw'):
                    old_pw = input.get('old_pw')
                    userdb_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])
                    user_info = userdb_obj.execute('SELECT %s FROM %s WHERE %s = "%s" LIMIT 1;' %(
                        env_db['PASSWORD_FIELD'], env_db['USERS_TABLE'], env_db['NICK_FIELD'], session.nickname))
                    userdb_obj.close()
                    if user_info:
                        user_info = user_info[0]
                        if user_info.has_key(env_db['PASSWORD_FIELD']):
                            if user_info.get(env_db['PASSWORD_FIELD']) == md5(old_pw):
                                partial_sql += ' %s = "%s", ' %(env_db['PASSWORD_FIELD'], md5(new_pw))
                            else:
                                 results_dic['info'].append('wrong old pass word')
                                 quit = True
                        else:
                             results_dic['info'].append('failed to get user info')
                             quit = True
                    else:
                        results_dic['info'] += ['no such user', ': ', session.nickname]
                        quit = True
                else:
                     results_dic['info'].append('old pass word is needed')
                     quit = True
            else:
                 results_dic['info'].append('pass word not well confirmed')
                 quit = True
        if quit:
            return WEB_RENDER('chusersettings', results = results_dic)
        elif partial_sql:
            userdb_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])
            sql_string = 'UPDATE %s SET %s WHERE %s = "%s";' %(
                    env_db['USERS_TABLE'], partial_sql.rstrip(', '), env_db['NICK_FIELD'], session.nickname)
            userdb_obj.execute(sql_string)
            userdb_obj.close()

            if new_nick:
                session.nickname = new_nick
            if new_email:
                session.username = new_email
            results_dic['reload_parent'] = True
            results_dic['info'].append('settings updated successfully')
            return WEB_RENDER('chusersettings', results_dic = results_dic)
        else:
            results_dic['info'].append('nothing to change')
            return WEB_RENDER('chusersettings', results_dic = results_dic)

class search:
    '''for structure search'''
    def __init__(self):
        # set default results to show per page
        self.results_per_page = int(session.results_per_page)
        # set max results number if it's not yet set
        self.max_results_num = int(session.max_results_num)
        # set the target language to session.lang
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'max_results_num': self.max_results_num,
            'trans_class': trans_class,
            'db_selected': is_selected('1'),
            'mode_selected': is_selected('2'),
            'query_id': '',
            'part_fields': [],
            'pri_and_struc_fields': {'pri_field': '', 'struc_field': ''},
            'results_search_type': '2',
            'lang': session.lang,
            'prequery': '',
            'html_title': 'normal search',
            'info': [],
            'current_page': 'search'
            } )

    def GET(self, name = ''):
        input = web.input()
        # results_mol_ids stores the mol ids found by the previous query
        results_of_get = []
        simi_values = []
        results_mol_ids = []
        results = []
        results_dic = self.results_dic
        search_mol = session.search_mol
        stored_results_of_post = ''
        stored_results_of_get = {}
        results_mol_ids = []
        query_info = {}
        query_mols_dic = {}
        adv_search_query = ''
        search_mol = ''
        md5_query = ''
        available_dbs = PUBLIC_DBS
        if session.authorized:
            available_dbs = DATABASES
            self.results_dic.update({'dbs': available_dbs})

        # check basic permission
        if not is_permited(session.userid, session.usergroup, ('s')):
            return html_no_permision(results_dic)

        try:
            if input.has_key('db') and input.get('db'):
                db_name = input.get('db')
                if db_name not in available_dbs:
                    return html_wrong_db(results_dic)
                session.db = db_name
            else:
                db_name = session.db

            if input.has_key('prequery') and input.get('prequery'):
                results_dic['prequery'] = input.get('prequery')

            env_db = ENVS[db_name]
            dbd_obj = dbd_objs[db_name]
            tables = dbd_obj.tables
            pri_field = env_db['PRI_FIELD']
            struc_field = env_db['2D_STRUC_FIELD']
            sql_fields_dic = env_db['FIELDS_TO_SHOW_DIC']
            fields_to_show_list_all = sql_fields_dic['all']
            fields_to_show_list_part = sql_fields_dic['part']
            part_fields = fields_to_show_list_part['fields']
            part_fields = [ re.sub(r'^[^\.]+\.', '', i) for i in part_fields ]
            table_heads = fields_to_show_list_part['comments']

            if input.has_key('query_id') and input.get('query_id'):
                md5_query = str(input.get('query_id'))

            if input.has_key('results_per_page'):
                self.results_per_page = int(input.get('results_per_page'))
                session.results_per_page = int(input.get('results_per_page'))
            if input.has_key('max_results_num'):
                self.max_results_num = int(input.get('max_results_num'))
                session.max_results_num = int(input.get('max_results_num'))

            search_type = session.search_mode
            if input.has_key('mode') and input.get('mode'):
                search_type = input.get('mode')
            else:
                search_type = session.search_mode
            results_dic['mode_selected'] = is_selected(search_type)

            if input.has_key('page'):
                # check if the results_of_get_file already exists
                # results_of_get_file is the results from the GET method of search class
                results_of_get_file = CACHE_PATH + '/' + md5_query + '.get'
                if os.path.exists(results_of_get_file):
                    if time.time() - os.path.getmtime(results_of_get_file) <= RESULTS_FILE_TIME_OUT:
                        f = open(results_of_get_file)
                        stored_results_of_get = pickle.load(f)
                        query_db = stored_results_of_get['query_info']['query_db']
                        if( not query_db in available_dbs ) or query_db != db_name:
                            return html_wrong_db(results_dic)
                        f.close()
                    else:
                        os.remove(results_of_get_file)
                else:
                    # post_results_file is the results from the POST method of search class
                    post_results_file = CACHE_PATH + '/' + md5_query + '.post'
                    if os.path.exists(post_results_file):
                        f = open(post_results_file)
                        stored_results_of_post = pickle.load(f)
                        f.close()
                        results_mol_ids = stored_results_of_post['query_results_ids']
                        simi_values = stored_results_of_post['simi_values']
                        query_info = stored_results_of_post['query_info']
                    else:
                        return web.seeother(URLS_DIC['search_url'])

                    if results_mol_ids:

                        db_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])
                        sql_obj = lm.sql(env_db)

                        if not pri_field in part_fields:
                            select_cols = tables[0] + '.' + pri_field + ', ' + ', '.join(fields_to_show_list_part['fields'])
                        else:
                            select_cols = ', '.join(fields_to_show_list_part['fields'])
                        query_string = 'SELECT %s FROM %s WHERE ( %s IN ( %s ) );' % (
                                select_cols,
                                sql_obj.gen_join_part_sql(tables, pri_field),
                                tables[0] + '.' + pri_field, ', '.join(results_mol_ids) )
                        time_before_search = time.time()
                        # this step is always fast, so no lock is set
                        results = db_obj.execute(query_string)
                        time_consumed = time.time() - time_before_search
                        query_info['time_consumed'] += time_consumed
                        db_obj.close()

                        simi_field = env_db['SIMI_FIELD']
                        for r in results:
                            tmpd = {}
                            mol_id = ''
                            if not pri_field in part_fields:
                                tmpd[pri_field] = r[pri_field]
                                mol_id = r[pri_field]

                            for j in fields_to_show_list_part['fields']:
                                j = re.sub(r'^[^\.]+\.', '', j)
                                if j in [ dbd_obj.get_field(k) for k in env_db['COMPRESSED_KEYS'] ]:
                                    # uncompress compressed entries
                                    if j == dbd_obj.get_field(env_db['2D_STRUC_KEY']):
                                        if session.removeh:
                                            mol = lm.mymol('mol', zlib.decompress(r[j])).removeh()
                                        else:
                                            mol = zlib.decompress(r[j])
                                        tmpd[j] = mol
                                    else:
                                        tmpd[j] = zlib.decompress(r[j])
                                elif j == pri_field:
                                    mol_id = r[j]
                                    tmpd[j] = mol_id
                                else:
                                    tmpd[j] = r[j]
                            if mol_id and simi_values and search_type == "3":
                                tmpd[simi_field] = simi_values[mol_id]
                            # l contains the mol info, each mol in a sublist: [ [...], [...] ]
                            results_of_get.append(tmpd)

                        if search_type == '3':
                            table_heads = fields_to_show_list_part['comments'] + ['simi value']
                            part_fields = fields_to_show_list_part['fields'] + [simi_field]
                            part_fields = [ re.sub(r'^[^\.]+\.', '', i) for i in part_fields ]
                            # sort the results on similarity
                            if simi_values:
                                results_of_get.sort( lambda e1, e2: - cmp(e1[simi_field], e2[simi_field]) )
                            for i in results_of_get:
                                i.update({simi_field: str(round(i[simi_field]*100, 2)) + '%'})

                    stored_results_of_get = {
                            'results_of_get': results_of_get,
                            'part_fields': part_fields,
                            'pri_and_struc_fields': {'pri_field': pri_field, 'struc_field': struc_field},
                            'table_heads': table_heads,
                            'query_info': query_info
                            }

                    # store the results
                    f = open(results_of_get_file, 'w')
                    pickle.dump(stored_results_of_get, f)
                    f.close()

                # results about to display
                query_info = stored_results_of_get['query_info']
                db_name = query_info['query_db']
                query_mols_dic = query_info['query_mols_dic']
                page = int(input.get('page'))
                results_of_get = stored_results_of_get['results_of_get']
                len_results = len(results_of_get)
                # calculate the page thing
                pages = ( lambda x, y: x % y and x / y + 1 or x / y ) (len_results, self.results_per_page)
                show_range_left = self.results_per_page * (page - 1)
                if show_range_left > len_results:
                    show_range_left = len_results - ( len_results % self.results_per_page )
                show_range_right = self.results_per_page * page

                # store the results in a dict
                results_dic.update({
                    'result_list': results_of_get[show_range_left:show_range_right],
                    'len_results': len_results,
                    'db': db_name,
                    'table_heads': stored_results_of_get['table_heads'],
                    'part_fields': stored_results_of_get['part_fields'],
                    'pri_and_struc_fields': stored_results_of_get['pri_and_struc_fields'],
                    'max_results_num': query_info['max_results_num'],
                    'pages': pages,
                    'page': page,
                    'min_simi': str(round(query_info['min_simi'], 2)),
                    'search_mol': query_info['query_mol'],
                    'query_mols_dic': query_info['query_mols_dic'],
                    'query_id': md5_query,
                    'time_consumed': round(query_info['time_consumed'], 2),
                    'adv_search_query': query_info['adv_search_query'],
                    'db_selected': is_selected(db_name),
                    'results_search_type': query_info['query_mode'],
                    'last_query_id': query_info['last_query_id'],
                    'last_db': query_info['last_db']
                    })
        except Exception, e:
            results_dic['info'].append('check your query')
            results_dic['info'].append(e)
            results_dic['html_title'] = 'query err'
            return html_info(results_dic)

        # set the title of the html page and render the results
        if search_type == "4":
            results_dic['html_title'] = 'advanced search'
            return html_advanced_search(results_dic)
        else:
            results_dic['html_title'] = 'normal search'
            return html_normal_search(results_dic)

    def POST(self, name = ''):
        # search types: 1: exact search, 2: substructure search,
        # 3: similarity search, 4: advanced search, 5: superstructure search
        input = web.input()
        results_dic = tpl_results_dic.copy()
        # check basic permission
        if not is_permited(session.userid, session.usergroup, ('s')):
            return html_no_permision(results_dic)

        query_smiles = ''
        adv_search_query = ''
        query_smiles_dic = {}
        query_mols_dic = {}
        max_results_num_from_query = 0
        # for similarity search
        min_simi = 0
        simi_values_dic = {}
        regex0 = ''
        regex1 = ''
        regex2 = ''
        last_mol_ids = []
        last_query_id = ''
        last_db = ''
        available_dbs = PUBLIC_DBS
        if session.authorized:
            available_dbs = DATABASES
            self.results_dic.update({'dbs': available_dbs})

        try:
            if input.has_key('results_per_page'):
                self.results_per_page = int(input.get('results_per_page'))
                session.results_per_page = int(input.get('results_per_page'))
            if input.has_key('max_results_num'):
                self.max_results_num = int(input.get('max_results_num'))
                session.max_results_num = int(input.get('max_results_num'))
            if input.has_key('mol'):
                search_mol = str(input.get('mol'))
                session.search_mol = str(input.get('mol'))
            else:
                search_mol = ''

            search_type = session.search_mode
            if input.has_key('mode') and input.get('mode'):
                if input.get('mode') in SEARCH_MODES:
                    search_type = input.get('mode')
                    session.search_mode = input.get('mode')
                else:
                    results_dic['info'] += ['invalid mode', input.get('mode')]
                    return html_info(results_dic)

            # chose which database to use
            if input.has_key('db') and input.get('db'):
                db_name = input.get('db')
                if db_name not in available_dbs:
                    return html_wrong_db(results_dic)
                session.db = input.get('db')
            else:
                db_name = session.db

            env_db = ENVS[db_name]
            sql_obj = lm.sql(env_db)
            dbd_obj = dbd_objs[db_name]
            tables = dbd_obj.tables
            pri_field = env_db['PRI_FIELD']
            smi_field = dbd_obj.get_field(env_db['SMILES_KEY'])
            simi_field = env_db['SIMI_FIELD']

            # in advanced mode, there could be more than one smiles and mols separated with "|".
            if search_type == "4":
                if input.has_key('query') and input.get('query'):
                    adv_search_query = query_preprocessing(str(input.get('query'))) + ' ' # add a space at the end for regex match
                    # recover escaped ' and ", for ' and " are legal in mode "4"
                    adv_search_query = re.sub(r'\\[\'\"]', '"', adv_search_query)
                else:
                    return html_query_imcomplete(results_dic)
                # get the smiless and mols from the input of advanced mode
                query_smiles_dic = {}
                query_mols_dic = {}
                if input.has_key('smiless') and input.get('smiless'):
                    for j in [ i for i in query_preprocessing(str(input.get('smiless'))).split('|') if i and i != '|' ]:
                        tmpl = j.split(':')
                        if len(tmpl) == 2:
                            query_smiles_dic[tmpl[0]] = tmpl[1]

                if input.has_key('mols') and input.get('mols'):
                    for j in [ i for i in query_preprocessing(str(input.get('mols'))).split('|') if i and i != '|' ]:
                        tmpl = j.split(':')
                        if len(tmpl) == 2:
                            query_mols_dic[tmpl[0]] = tmpl[1]
                # store in session
                if query_smiles_dic:
                    session.query_smiles_dic = query_smiles_dic
                if query_mols_dic:
                    session.query_mols_dic = query_mols_dic

                # check if the query legal
                # first check if there are key words what are not in the abbr_dic
                regex0 = re.compile(r'([><=!~]+ *[^ )(]+[ )(]*)|([)(])|([sS][uU][bBpP])|([mM][aA][xX])|([aA][nN][dD])|([oO][rR])|([nN][oR][tT])')
                key_words = []
                key_words = list(set(regex0.sub(' ', adv_search_query).split()))
                for k in key_words:
                    if not k in env_db['ABBR_DIC'].keys():
                        results_dic = self.results_dic
                        results_dic['info'].append('contains illegal words')
                        results_dic['info'].append(': ' + k)
                        results_dic['html_title'] = 'query err'
                        return html_info(results_dic)
                # second check if the mol buffer contains all needed molecules
                regex1 = re.compile(r'[sS][uU][bBpP] *[!=]+ *[^ )(]*(?=[ )(]+)')
                mol_key = ''
                for i in regex1.findall(adv_search_query):
                    mol_key = i.split('=')[-1].strip(' ')
                    if not ( query_smiles_dic.has_key(mol_key) and query_smiles_dic[mol_key] ):
                        results_dic = self.results_dic
                        results_dic['info'].append('mol buffer imcomplete')
                        results_dic['html_title'] = 'query err'
                        return html_info(results_dic)

                # replace some words (~ to like) and abstract the max (limit) value if it has
                new_adv_search_query = adv_search_query.replace('~', ' LIKE ')
                regex2 = re.compile(r'[mM][aA][xX] *=+ *[^ )(]*(?=[ )(]+)')
                tmpl = regex2.findall(new_adv_search_query)
                if len(tmpl) == 1:
                    try:
                        max_results_num_from_query = int(tmpl[0].split('=')[-1].strip(' '))
                    except:
                        pass
                new_adv_search_query = regex2.sub('', new_adv_search_query)

                try:
                    query_sql = sql_obj.gen_adv_search_sql(new_adv_search_query, query_smiles_dic, env_db['ABBR_DIC'])
                except Exception, e:
                    results_dic['info'] += ['query err', e]
                    return html_info(results_dic)
            elif input.has_key('smiles') and input.get('smiles'):
                query_smiles = query_preprocessing(str(input.get('smiles')))
                if search_type == "3":
                    if input.has_key('min_simi') and input.get("min_simi"):
                        try:
                            min_simi = float(input.get("min_simi"))
                        except:
                            results_dic = self.results_dic
                            results_dic['info'].append('min simi contains illegal char')
                            results_dic['html_title'] = 'query err'
                            return html_info(results_dic)
                    else:
                        return html_query_imcomplete(results_dic)
                    query_sql = sql_obj.gen_simi_search_sql(query_smiles, min_simi)
                else:
                    if search_type == '1':
                        type = '1'
                    elif search_type == '2':
                        type = '2'
                    elif search_type == '5':
                        type = '4'
                    query_sql = sql_obj.gen_search_sql(query_smiles, type)
            else:
                return html_query_imcomplete(results_dic)

            db_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])

            results = []
            results_tmp = True

            # search in results
            if input.has_key('search_in_results') and input.get('search_in_results'):
                last_results_of_post_file = CACHE_PATH + '/' + input.get('search_in_results') + '.post'
                if os.path.exists(last_results_of_post_file):
                    f = open(last_results_of_post_file)
                    last_results_of_post = pickle.load(f)
                    f.close()
                    last_mol_ids = last_results_of_post['query_results_ids']
                    last_query_info = last_results_of_post['query_info']
                    last_query_id = last_query_info['query_id']
                    last_db = last_query_info['query_db']

            # generates the sql string for query
            if last_mol_ids:
                query_string = 'SELECT %s, %s %s AND %s IN (%s)' % (
                        tables[0] + '.' + pri_field,
                        smi_field,
                        query_sql,
                        tables[0] + '.' + pri_field,
                        ', '.join(last_mol_ids) )
            else:
                query_string = 'SELECT %s, %s %s' % (
                        tables[0] + '.' + pri_field,
                        smi_field,
                        query_sql)

            # check if there's already a results file
            md5_query = md5(query_string + db_name + search_type)
            session.md5_query = md5_query
            results_of_post_file = CACHE_PATH + '/' + md5_query + '.post'
            lock_file = results_of_post_file + '.lock'
            if os.path.exists(results_of_post_file):
                if time.time() - os.path.getmtime(results_of_post_file) >= RESULTS_FILE_TIME_OUT:
                    os.remove(results_of_post_file)
                else:
                    return web.seeother(URLS_DIC['search_url'] + '?page=1&db=%s&query_id=%s' %(db_name, md5_query))

            # check if the lock file exists, if exists then wait, else continue.
            while os.path.exists(lock_file):
                # check if the life span of lock_file reached
                if time.time() - os.path.getmtime(lock_file) >= LOCK_FILE_LIFE_SPAN:
                    os.remove(lock_file)
                else:
                    time.sleep(5)

            # define filters
            filter = None
            if search_type == "1":
                def filter(results_dict, mol_obj = lm.mymol('smi', query_smiles), smiles_field = smi_field):
                    if results_dict.has_key(smiles_field):
                        return mol_obj.gen_openbabel_can_smiles() == results_dict[smiles_field]
                    return False
            elif search_type == "2":
                def filter(results_dict, mol_obj = lm.mymol('smi', query_smiles), smiles_field = smi_field):
                    if results_dict.has_key(smiles_field):
                        return mol_obj.sub_match('smi', results_dict[smiles_field])
                    return False
            elif search_type == "3":
                # similarity search actually needs no filter.
                pass
            elif search_type == '4':
                sub_smiles = []
                sup_smiles = []
                sub_m_objs = []
                sup_m_objs = []
                re_sub = re.compile(r'[sS][uU][bB] *[!=]+ *[^ )(]*(?=[ )(]+)')
                re_sup = re.compile(r'[sS][uU][pP] *[!=]+ *[^ )(]*(?=[ )(]+)')
                for i in re_sub.findall(adv_search_query):
                    # for querying for a molecule contains no a paticular substructure always
                    # filters out some positive ones, so it's no need to filter here any more,
                    # hence we exclude those '!=' ones here.
                    if re.findall(r'!=', i):
                        continue
                    elif re.findall(r'[^!]=', i):
                        mol_key = i.split('=')[-1].strip(' ')
                        if query_smiles_dic.has_key(mol_key) and query_smiles_dic[mol_key]:
                            sub_smiles.append(query_smiles_dic[mol_key])
                for i in re_sup.findall(adv_search_query):
                    # for querying for the superstructure of a paticular molecule always
                    # filters out some positive ones, so it's no need to filter here any more,
                    # hence we exclude those '!=' ones here.
                    if re.findall(r'!=', i):
                        continue
                    elif re.findall(r'[^!]=', i):
                        mol_key = i.split('=')[-1].strip(' ')
                        if query_smiles_dic.has_key(mol_key) and query_smiles_dic[mol_key]:
                            sup_smiles.append(query_smiles_dic[mol_key])

                sub_m_objs = [ lm.mymol('smi', m) for m in sub_smiles ]
                sup_m_objs = [ lm.mymol('smi', m) for m in sup_smiles ]

                # filter is only needed to define when the m_objs list is not empty.
                if sub_m_objs or sup_m_objs:
                    def filter(results_dict,
                            sub_mol_objs = sub_m_objs,
                            sup_mol_objs = sup_m_objs,
                            smiles_field = smi_field):
                        if results_dict.has_key(smiles_field):
                            for i in sub_mol_objs:
                                if not i.sub_match('smi', results_dict[smiles_field]):
                                    return False
                            for i in sup_mol_objs:
                                if not i.sup_match('smi', results_dict[smiles_field]):
                                    return False
                            return True
                        return False

            elif search_type == '5':
                def filter(results_dict, mol_obj = lm.mymol('smi', query_smiles), smiles_field = smi_field):
                    if results_dict.has_key(smiles_field):
                        return mol_obj.sup_match('smi', results_dict[smiles_field])
                    return False

            # limit the results
            if max_results_num_from_query:
                num_per_select = 150
                max_results_num = max_results_num_from_query
            elif search_type == '3':
                max_results_num = 10
            else:
                num_per_select = 150
                max_results_num = self.max_results_num

            # search in database and filter the reuslts
            # record time consuming
            time_before_search = time.time()
            if search_type in ('1', '3'):
                if search_type == '1':
                    limit = '' #' LIMIT 1'
                elif search_type == '3':
                    limit = ' LIMIT %s ' %(max_results_num,)
                # set lock to avoid duplocated search
                open(lock_file, 'w')
                results = db_obj.execute(query_string + limit + ';')
                if os.path.exists(lock_file):
                    os.remove(lock_file)

                db_obj.close()
            elif search_type in ('2', '4', '5'):
                # set lock to avoid duplocated search
                open(lock_file, 'w')
                results = db_obj.query(
                        query_string,
                        filter,
                        tables[0] + '.' + pri_field,
                        max_results_num,
                        num_per_select)
                if os.path.exists(lock_file):
                    os.remove(lock_file)

                db_obj.close()

            time_consumed = time.time() - time_before_search

            # preprocessing the results to store
            # cut of the extra results
            results = results[:max_results_num]
            results_dic_to_store = {}
            mol_id_to_store = []
            query_info = {}
            for r in results:
                if r.has_key(pri_field):
                    id = r[pri_field]
                    mol_id_to_store.append(str(id))
                    if r.has_key(simi_field):
                        simi_values_dic[id] = r[simi_field]
            query_info = {
                    'query_mols_dic': query_mols_dic,
                    'query_smiles_dic': query_smiles_dic,
                    'query_smiles': query_smiles,
                    'query_mol': search_mol,
                    'query_string': query_string,
                    'query_db': db_name,
                    'max_results_num': max_results_num,
                    'adv_search_query': adv_search_query,
                    'query_mode': search_type,
                    'min_simi': min_simi,
                    'time_consumed': time_consumed,
                    'last_query_id': last_query_id,
                    'last_db': last_db,
                    'query_id': md5_query
                    }
            results_dic_to_store = {
                    'query_results_ids': mol_id_to_store,
                    'simi_values': simi_values_dic,
                    'query_info': query_info
                    }
            # store search results
            f = open(results_of_post_file, 'w')
            pickle.dump(results_dic_to_store, f)
            f.close()
            return web.seeother(URLS_DIC['search_url'] + '?page=1&db=%s&query_id=%s' %(db_name, md5_query))
        except Exception, e:
            results_dic = self.results_dic
            results_dic['info'].append('check your query')
            results_dic['info'].append(e)
            results_dic['html_title'] = 'query err'
            return html_info(results_dic)

class webapi:
    '''web api for structure search'''
    def __init__(self):
        # set default results to show per page
        self.results_per_page = int(session.results_per_page)
        # set max results number if it's not yet set
        self.max_results_num = int(session.max_results_num)
        # set the target language to session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'max_results_num': self.max_results_num,
            'query_id': '',
            'part_fields': [],
            'pri_and_struc_fields': {'pri_field': '', 'struc_field': ''},
            'results_search_type': '2',
            'prequery': '',
            'info': [],
            } )

    def GET(self, name = ''):
        input = web.input()
        # results_mol_ids stores the mol ids found by the previous query
        results_of_get = []
        simi_values = []
        results_mol_ids = []
        results = []
        results_dic = self.results_dic
        search_mol = session.search_mol
        stored_results_of_post = ''
        stored_results_of_get = {}
        results_mol_ids = []
        query_info = {}
        query_mols_dic = {}
        adv_search_query = ''
        search_mol = ''
        md5_query = ''
        available_dbs = PUBLIC_DBS
        if session.authorized:
            available_dbs = DATABASES
            self.results_dic.update({'dbs': available_dbs})

        # check basic permission
        if not is_permited(session.userid, session.usergroup, ('s')):
            return json.dumps({'status': 'Permition denied'})

        try:
            if input.has_key('db') and input.get('db'):
                db_name = input.get('db')
                if db_name not in available_dbs:
                    return json.dumps({'status': 'DB not accessible!'})
                session.db = db_name
            else:
                db_name = session.db

            if input.has_key('prequery') and input.get('prequery'):
                results_dic['prequery'] = input.get('prequery')

            env_db = ENVS[db_name]
            dbd_obj = dbd_objs[db_name]
            tables = dbd_obj.tables
            pri_field = env_db['PRI_FIELD']
            struc_field = env_db['2D_STRUC_FIELD']
            sql_fields_dic = env_db['FIELDS_TO_SHOW_DIC']
            fields_to_show_list_all = sql_fields_dic['all']
            fields_to_show_list_part = sql_fields_dic['part']
            part_fields = fields_to_show_list_part['fields']
            part_fields = [ re.sub(r'^[^\.]+\.', '', i) for i in part_fields ]
            table_heads = fields_to_show_list_part['comments']

            if input.has_key('query_id') and input.get('query_id'):
                md5_query = str(input.get('query_id'))

            if input.has_key('results_per_page'):
                self.results_per_page = int(input.get('results_per_page'))
                session.results_per_page = int(input.get('results_per_page'))
            if input.has_key('max_results_num'):
                self.max_results_num = int(input.get('max_results_num'))
                session.max_results_num = int(input.get('max_results_num'))

            search_type = session.search_mode
            if input.has_key('mode') and input.get('mode'):
                search_type = input.get('mode')
            else:
                search_type = session.search_mode

            if input.has_key('page'):
                # check if the results_of_get_file already exists
                # results_of_get_file is the results from the GET method of search class
                results_of_get_file = CACHE_PATH + '/' + md5_query + '.get'
                if os.path.exists(results_of_get_file):
                    if time.time() - os.path.getmtime(results_of_get_file) <= RESULTS_FILE_TIME_OUT:
                        f = open(results_of_get_file)
                        stored_results_of_get = pickle.load(f)
                        query_db = stored_results_of_get['query_info']['query_db']
                        if( not query_db in available_dbs ) or query_db != db_name:
                            return json.dumps({'status': 'DB not accessible!'})
                        f.close()
                    else:
                        os.remove(results_of_get_file)
                else:
                    # post_results_file is the results from the POST method of search class
                    post_results_file = CACHE_PATH + '/' + md5_query + '.post'
                    if os.path.exists(post_results_file):
                        f = open(post_results_file)
                        stored_results_of_post = pickle.load(f)
                        f.close()
                        results_mol_ids = stored_results_of_post['query_results_ids']
                        simi_values = stored_results_of_post['simi_values']
                        query_info = stored_results_of_post['query_info']
                    else:
                        return json.dumps({'status': 'Not yet posted!'})

                    if results_mol_ids:

                        db_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])
                        sql_obj = lm.sql(env_db)

                        if not pri_field in part_fields:
                            select_cols = tables[0] + '.' + pri_field + ', ' + ', '.join(fields_to_show_list_part['fields'])
                        else:
                            select_cols = ', '.join(fields_to_show_list_part['fields'])
                        query_string = 'SELECT %s FROM %s WHERE ( %s IN ( %s ) );' % (
                                select_cols,
                                sql_obj.gen_join_part_sql(tables, pri_field),
                                tables[0] + '.' + pri_field, ', '.join(results_mol_ids) )
                        time_before_search = time.time()
                        # this step is always fast, so no lock is set
                        results = db_obj.execute(query_string)
                        time_consumed = time.time() - time_before_search
                        query_info['time_consumed'] += time_consumed
                        db_obj.close()

                        simi_field = env_db['SIMI_FIELD']
                        for r in results:
                            tmpd = {}
                            mol_id = ''
                            if not pri_field in part_fields:
                                tmpd[pri_field] = r[pri_field]
                                mol_id = r[pri_field]

                            for j in fields_to_show_list_part['fields']:
                                j = re.sub(r'^[^\.]+\.', '', j)
                                if j in [ dbd_obj.get_field(k) for k in env_db['COMPRESSED_KEYS'] ]:
                                    # uncompress compressed entries
                                    if j == dbd_obj.get_field(env_db['2D_STRUC_KEY']):
                                        if session.removeh:
                                            mol = lm.mymol('mol', zlib.decompress(r[j])).removeh()
                                        else:
                                            mol = zlib.decompress(r[j])
                                        tmpd[j] = mol
                                    else:
                                        tmpd[j] = zlib.decompress(r[j])
                                elif j == pri_field:
                                    mol_id = r[j]
                                    tmpd[j] = mol_id
                                else:
                                    tmpd[j] = r[j]
                            if mol_id and simi_values and search_type == "3":
                                tmpd[simi_field] = simi_values[mol_id]
                            # l contains the mol info, each mol in a sublist: [ [...], [...] ]
                            results_of_get.append(tmpd)

                        if search_type == '3':
                            table_heads = fields_to_show_list_part['comments'] + ['simi value']
                            part_fields = fields_to_show_list_part['fields'] + [simi_field]
                            part_fields = [ re.sub(r'^[^\.]+\.', '', i) for i in part_fields ]
                            # sort the results on similarity
                            if simi_values:
                                results_of_get.sort( lambda e1, e2: - cmp(e1[simi_field], e2[simi_field]) )
                            for i in results_of_get:
                                i.update({simi_field: str(round(i[simi_field]*100, 2)) + '%'})

                    stored_results_of_get = {
                            'results_of_get': results_of_get,
                            'part_fields': part_fields,
                            'pri_and_struc_fields': {'pri_field': pri_field, 'struc_field': struc_field},
                            'table_heads': table_heads,
                            'query_info': query_info
                            }

                    # store the results
                    f = open(results_of_get_file, 'w')
                    pickle.dump(stored_results_of_get, f)
                    f.close()

                # results about to display
                query_info = stored_results_of_get['query_info']
                db_name = query_info['query_db']
                query_mols_dic = query_info['query_mols_dic']
                page = int(input.get('page'))
                results_of_get = stored_results_of_get['results_of_get']
                len_results = len(results_of_get)
                # calculate the page thing
                pages = ( lambda x, y: x % y and x / y + 1 or x / y ) (len_results, self.results_per_page)
                show_range_left = self.results_per_page * (page - 1)
                if show_range_left > len_results:
                    show_range_left = len_results - ( len_results % self.results_per_page )
                show_range_right = self.results_per_page * page

                # store the results in a dict
                results_dic.update({
                    'result_list': results_of_get[show_range_left:show_range_right],
                    'len_results': len_results,
                    'db': db_name,
                    'table_heads': stored_results_of_get['table_heads'],
                    'part_fields': stored_results_of_get['part_fields'],
                    'pri_and_struc_fields': stored_results_of_get['pri_and_struc_fields'],
                    'max_results_num': query_info['max_results_num'],
                    'pages': pages,
                    'page': page,
                    'min_simi': str(round(query_info['min_simi'], 2)),
                    'search_mol': query_info['query_mol'],
                    'query_mols_dic': query_info['query_mols_dic'],
                    'query_id': md5_query,
                    'time_consumed': round(query_info['time_consumed'], 2),
                    'adv_search_query': query_info['adv_search_query'],
                    'results_search_type': query_info['query_mode'],
                    'last_query_id': query_info['last_query_id'],
                    'last_db': query_info['last_db']
                    })
        except Exception, e:
            results_dic['info'].append('check your query')
            results_dic['info'].append(e)
            return json.dumps(results_dic)

        for key in ('mode_selected', 'db_selected',
                'links', 'urls_dic', 'table_heads',
                'last_db', 'part_fields', 'pri_and_struc_fields',
                'lang', 'trans_class', 'info_head',
                'html_title', 'current_page'):
            self.results_dic.pop(key)
        return json.dumps(results_dic)

    def POST(self, name = ''):
        # search types: 1: exact search, 2: substructure search,
        # 3: similarity search, 4: advanced search, 5: superstructure search
        input_raw = web.input()
        if input_raw.has_key('query_format'):
            qfmt = input_raw.get('query_format')
            if qfmt == 'json' and input_raw.has_key('json'):
                input = json.loads(input_raw.get('json'))
            else:
                input = input_raw
        else:
            input = input_raw

        results_dic = tpl_results_dic.copy()
        # check basic permission
        if not is_permited(session.userid, session.usergroup, ('s')):
            return json.dumps({'status': 'Permition denied!'})

        query_smiles = ''
        adv_search_query = ''
        query_smiles_dic = {}
        query_mols_dic = {}
        max_results_num_from_query = 0
        # for similarity search
        min_simi = 0
        simi_values_dic = {}
        regex0 = ''
        regex1 = ''
        regex2 = ''
        last_mol_ids = []
        last_query_id = ''
        last_db = ''
        available_dbs = PUBLIC_DBS
        if session.authorized:
            available_dbs = DATABASES
            self.results_dic.update({'dbs': available_dbs})

        try:
            if input.has_key('results_per_page'):
                self.results_per_page = int(input.get('results_per_page'))
                session.results_per_page = int(input.get('results_per_page'))
            if input.has_key('max_results_num'):
                self.max_results_num = int(input.get('max_results_num'))
                session.max_results_num = int(input.get('max_results_num'))
            if input.has_key('mol'):
                search_mol = str(input.get('mol'))
                session.search_mol = str(input.get('mol'))
            else:
                search_mol = ''

            search_type = session.search_mode
            if input.has_key('mode') and input.get('mode'):
                if input.get('mode') in SEARCH_MODES:
                    search_type = input.get('mode')
                    session.search_mode = input.get('mode')
                else:
                    return json.dumps({'status': 'Invalid mode: %s' %input.get('mode')})

            # chose which database to use
            if input.has_key('db') and input.get('db'):
                db_name = input.get('db')
                if db_name not in available_dbs:
                    return json.dumps({'status': 'DB not accessible!'})
                session.db = input.get('db')
            else:
                db_name = session.db

            env_db = ENVS[db_name]
            sql_obj = lm.sql(env_db)
            dbd_obj = dbd_objs[db_name]
            tables = dbd_obj.tables
            pri_field = env_db['PRI_FIELD']
            smi_field = dbd_obj.get_field(env_db['SMILES_KEY'])
            simi_field = env_db['SIMI_FIELD']

            # in advanced mode, there could be more than one smiles and mols separated with "|".
            if search_type == "4":
                if input.has_key('query') and input.get('query'):
                    adv_search_query = query_preprocessing(str(input.get('query'))) + ' ' # add a space at the end for regex match
                    # recover escaped ' and ", for ' and " are legal in mode "4"
                    adv_search_query = re.sub(r'\\[\'\"]', '"', adv_search_query)
                else:
                    return json.dumps({'status': 'Query imcomplete!'})
                # get the smiless and mols from the input of advanced mode
                query_smiles_dic = {}
                query_mols_dic = {}
                if input.has_key('smiless') and input.get('smiless'):
                    for j in [ i for i in query_preprocessing(str(input.get('smiless'))).split('|') if i and i != '|' ]:
                        tmpl = j.split(':')
                        if len(tmpl) == 2:
                            query_smiles_dic[tmpl[0]] = tmpl[1]
                elif input.has_key('mols') and input.get('mols'):
                    for j in [ i for i in query_preprocessing(str(input.get('mols'))).split('|') if i and i != '|' ]:
                        tmpl = j.split(':')
                        if len(tmpl) == 2:
                            query_mols_dic[tmpl[0]] = tmpl[1]

                # store in session
                if query_smiles_dic:
                    session.query_smiles_dic = query_smiles_dic
                elif query_mols_dic:
                    for k, v in query_smiles_dic.items():
                        query_smiles_dic[k] = lm.mymol('mol', v).mol.write('smi')
                if query_smiles_dic:
                    session.query_smiles_dic = query_smiles_dic
                if query_mols_dic:
                    session.query_mols_dic = query_mols_dic

                # check if the query legal
                # first check if there are key words what are not in the abbr_dic
                regex0 = re.compile(r'([><=!~]+ *[^ )(]+[ )(]*)|([)(])|([sS][uU][bBpP])|([mM][aA][xX])|([aA][nN][dD])|([oO][rR])|([nN][oR][tT])')
                key_words = []
                key_words = list(set(regex0.sub(' ', adv_search_query).split()))
                for k in key_words:
                    if not k in env_db['ABBR_DIC'].keys():
                        return json.dumps({'status': 'Contains illegal words!'})
                # second check if the mol buffer contains all needed molecules
                regex1 = re.compile(r'[sS][uU][bBpP] *[!=]+ *[^ )(]*(?=[ )(]+)')
                mol_key = ''
                for i in regex1.findall(adv_search_query):
                    mol_key = i.split('=')[-1].strip(' ')
                    if not ( query_smiles_dic.has_key(mol_key) and query_smiles_dic[mol_key] ):
                        return json.dumps({'status': 'Mol buffer imcomplete!'})

                # replace some words (~ to like) and abstract the max (limit) value if it has
                new_adv_search_query = adv_search_query.replace('~', ' LIKE ')
                regex2 = re.compile(r'[mM][aA][xX] *=+ *[^ )(]*(?=[ )(]+)')
                tmpl = regex2.findall(new_adv_search_query)
                if len(tmpl) == 1:
                    try:
                        max_results_num_from_query = int(tmpl[0].split('=')[-1].strip(' '))
                    except:
                        pass
                new_adv_search_query = regex2.sub('', new_adv_search_query)

                try:
                    query_sql = sql_obj.gen_adv_search_sql(new_adv_search_query, query_smiles_dic, env_db['ABBR_DIC'])
                except Exception, e:
                    return json.dumps({'status': 'Query error: %s' %str(e)})
            elif (input.has_key('mol') and input.get('mol')) or (input.has_key('smiles') and input.get('smiles')):
                if input.has_key('smiles') and input.get('smiles'):
                    query_smiles = input.get('smiles')
                else:
                    query_smiles = query_preprocessing(lm.mymol('mol', str(input.get('mol'))).mol.write('smi'))
                if search_type == "3":
                    if input.has_key('min_simi') and input.get("min_simi"):
                        try:
                            min_simi = float(input.get("min_simi"))
                        except:
                            return json.dumps({'status': 'Min simi contains illegal char!'})
                    else:
                        return json.dumps({'status': 'Query imcomplete!'})
                    query_sql = sql_obj.gen_simi_search_sql(query_smiles, min_simi)
                else:
                    if search_type == '1':
                        type = '1'
                    elif search_type == '2':
                        type = '2'
                    elif search_type == '5':
                        type = '4'
                    query_sql = sql_obj.gen_search_sql(query_smiles, type)
            else:
                return json.dumps({'status': 'Query imcomplete!'})

            db_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])

            results = []
            results_tmp = True

            # search in results
            if input.has_key('search_in_results') and input.get('search_in_results'):
                last_results_of_post_file = CACHE_PATH + '/' + input.get('search_in_results') + '.post'
                if os.path.exists(last_results_of_post_file):
                    f = open(last_results_of_post_file)
                    last_results_of_post = pickle.load(f)
                    f.close()
                    last_mol_ids = last_results_of_post['query_results_ids']
                    last_query_info = last_results_of_post['query_info']
                    last_query_id = last_query_info['query_id']
                    last_db = last_query_info['query_db']

            # generates the sql string for query
            if last_mol_ids:
                query_string = 'SELECT %s, %s %s AND %s IN (%s)' % (
                        tables[0] + '.' + pri_field,
                        smi_field,
                        query_sql,
                        tables[0] + '.' + pri_field,
                        ', '.join(last_mol_ids) )
            else:
                query_string = 'SELECT %s, %s %s' % (
                        tables[0] + '.' + pri_field,
                        smi_field,
                        query_sql)

            # check if there's already a results file
            md5_query = md5(query_string + db_name + search_type)
            session.md5_query = md5_query
            results_of_post_file = CACHE_PATH + '/' + md5_query + '.post'
            lock_file = results_of_post_file + '.lock'
            if os.path.exists(results_of_post_file):
                if time.time() - os.path.getmtime(results_of_post_file) >= RESULTS_FILE_TIME_OUT:
                    os.remove(results_of_post_file)
                else:
                    return json.dumps({'status': 'OK',
                        'result_url': URLS_DIC['webapi_url'] + '?page=1&db=%s&query_id=%s' %(db_name, md5_query)})

            # check if the lock file exists, if exists then wait, else continue.
            while os.path.exists(lock_file):
                # check if the life span of lock_file reached
                if time.time() - os.path.getmtime(lock_file) >= LOCK_FILE_LIFE_SPAN:
                    os.remove(lock_file)
                else:
                    time.sleep(5)

            # define filters
            filter = None
            if search_type == "1":
                def filter(results_dict, mol_obj = lm.mymol('smi', query_smiles), smiles_field = smi_field):
                    if results_dict.has_key(smiles_field):
                        return mol_obj.gen_openbabel_can_smiles() == results_dict[smiles_field]
                    return False
            elif search_type == "2":
                def filter(results_dict, mol_obj = lm.mymol('smi', query_smiles), smiles_field = smi_field):
                    if results_dict.has_key(smiles_field):
                        return mol_obj.sub_match('smi', results_dict[smiles_field])
                    return False
            elif search_type == "3":
                # similarity search actually needs no filter.
                pass
            elif search_type == '4':
                sub_smiles = []
                sup_smiles = []
                sub_m_objs = []
                sup_m_objs = []
                re_sub = re.compile(r'[sS][uU][bB] *[!=]+ *[^ )(]*(?=[ )(]+)')
                re_sup = re.compile(r'[sS][uU][pP] *[!=]+ *[^ )(]*(?=[ )(]+)')
                for i in re_sub.findall(adv_search_query):
                    # for querying for a molecule contains no a paticular substructure always
                    # filters out some positive ones, so it's no need to filter here any more,
                    # hence we exclude those '!=' ones here.
                    if re.findall(r'!=', i):
                        continue
                    elif re.findall(r'[^!]=', i):
                        mol_key = i.split('=')[-1].strip(' ')
                        if query_smiles_dic.has_key(mol_key) and query_smiles_dic[mol_key]:
                            sub_smiles.append(query_smiles_dic[mol_key])
                for i in re_sup.findall(adv_search_query):
                    # for querying for the superstructure of a paticular molecule always
                    # filters out some positive ones, so it's no need to filter here any more,
                    # hence we exclude those '!=' ones here.
                    if re.findall(r'!=', i):
                        continue
                    elif re.findall(r'[^!]=', i):
                        mol_key = i.split('=')[-1].strip(' ')
                        if query_smiles_dic.has_key(mol_key) and query_smiles_dic[mol_key]:
                            sup_smiles.append(query_smiles_dic[mol_key])

                sub_m_objs = [ lm.mymol('smi', m) for m in sub_smiles ]
                sup_m_objs = [ lm.mymol('smi', m) for m in sup_smiles ]

                # filter is only needed to define when the m_objs list is not empty.
                if sub_m_objs or sup_m_objs:
                    def filter(results_dict,
                            sub_mol_objs = sub_m_objs,
                            sup_mol_objs = sup_m_objs,
                            smiles_field = smi_field):
                        if results_dict.has_key(smiles_field):
                            for i in sub_mol_objs:
                                if not i.sub_match('smi', results_dict[smiles_field]):
                                    return False
                            for i in sup_mol_objs:
                                if not i.sup_match('smi', results_dict[smiles_field]):
                                    return False
                            return True
                        return False

            elif search_type == '5':
                def filter(results_dict, mol_obj = lm.mymol('smi', query_smiles), smiles_field = smi_field):
                    if results_dict.has_key(smiles_field):
                        return mol_obj.sup_match('smi', results_dict[smiles_field])
                    return False

            # limit the results
            if max_results_num_from_query:
                num_per_select = 150
                max_results_num = max_results_num_from_query
            elif search_type == '3':
                max_results_num = 10
            else:
                num_per_select = 150
                max_results_num = self.max_results_num

            # search in database and filter the reuslts
            # record time consuming
            time_before_search = time.time()
            if search_type in ('1', '3'):
                if search_type == '1':
                    limit = '' #' LIMIT 1'
                elif search_type == '3':
                    limit = ' LIMIT %s ' %(max_results_num,)
                # set lock to avoid duplocated search
                open(lock_file, 'w')
                results = db_obj.execute(query_string + limit + ';')
                if os.path.exists(lock_file):
                    os.remove(lock_file)

                db_obj.close()
            elif search_type in ('2', '4', '5'):
                # set lock to avoid duplocated search
                open(lock_file, 'w')
                results = db_obj.query(
                        query_string,
                        filter,
                        tables[0] + '.' + pri_field,
                        max_results_num,
                        num_per_select)
                if os.path.exists(lock_file):
                    os.remove(lock_file)

                db_obj.close()

            time_consumed = time.time() - time_before_search

            # preprocessing the results to store
            # cut of the extra results
            results = results[:max_results_num]
            results_dic_to_store = {}
            mol_id_to_store = []
            query_info = {}
            for r in results:
                if r.has_key(pri_field):
                    id = r[pri_field]
                    mol_id_to_store.append(str(id))
                    if r.has_key(simi_field):
                        simi_values_dic[id] = r[simi_field]
            query_info = {
                    'query_mols_dic': query_mols_dic,
                    'query_smiles_dic': query_smiles_dic,
                    'query_smiles': query_smiles,
                    'query_mol': search_mol,
                    'query_string': query_string,
                    'query_db': db_name,
                    'max_results_num': max_results_num,
                    'adv_search_query': adv_search_query,
                    'query_mode': search_type,
                    'min_simi': min_simi,
                    'time_consumed': time_consumed,
                    'last_query_id': last_query_id,
                    'last_db': last_db,
                    'query_id': md5_query
                    }
            results_dic_to_store = {
                    'query_results_ids': mol_id_to_store,
                    'simi_values': simi_values_dic,
                    'query_info': query_info
                    }
            # store search results
            f = open(results_of_post_file, 'w')
            pickle.dump(results_dic_to_store, f)
            f.close()
            return json.dumps({'status': 'OK',
                'result_url': URLS_DIC['webapi_url'] + '?page=1&db=%s&query_id=%s' %(db_name, md5_query)})
        except Exception, e:
            return json.dumps({'status': 'Query error: %s' %str(e)})

class molinfo:
    def __init__(self):
        # set the target language to session.lang
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'mode_selected': is_selected(str(session.search_mode)),
            'html_title': 'mol info',
            'info': [],
            'show_edit': False,
            'current_page': 'search',
            'lang': session.lang
            } )
    def GET(self, name = ''):
        input = web.input()
        results_dic = self.results_dic
        available_dbs = PUBLIC_DBS
        if session.authorized:
            available_dbs = DATABASES
            self.results_dic.update({'dbs': available_dbs})

        # check basic permission
        if not is_permited(session.userid, session.usergroup, ('s')):
            return html_no_permision(results_dic)

        # chose which database to use
        if input.has_key('db') and input.get('db'):
            db_name = input.get('db')
            if db_name not in available_dbs:
                return html_wrong_db(results_dic)
            session.db = db_name
        else:
            db_name = session.db

        env_db = ENVS[db_name]
        sql_obj = lm.sql(env_db)
        sql_fields_dic = env_db['FIELDS_TO_SHOW_DIC']
        fields_to_show_list_all = sql_fields_dic['all']
        fields_to_show_list_part = sql_fields_dic['part']
        dbd_obj = dbd_objs[db_name]
        tables = dbd_obj.tables
        pri_field = env_db['PRI_FIELD']
        smi_field = dbd_obj.get_field(env_db['SMILES_KEY'])
        simi_field = env_db['SIMI_FIELD']

        try:
            if input.has_key('mol_id'):
                mol_id = query_preprocessing(str(input.get('mol_id')))
                if not re.match('^[0-9]+$', mol_id):
                    return html_query_illegal(results_dic)

                db_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])

                query_string = 'SELECT %s FROM %s WHERE ( %s = %s ) LIMIT 1;' % (
                        ', '.join(fields_to_show_list_all['fields']),
                        sql_obj.gen_join_part_sql(tables, pri_field),
                        tables[0] + '.' + pri_field,
                        mol_id )
                results = db_obj.execute(query_string)
                db_obj.close()
                if not results:
                    results_dic['info'].append('no mol to show')
                    return html_info(results_dic)
                else:
                    results = results[0]

                    # change the decimal submiter id to nick name
                    submiter_field = dbd_obj.get_field(env_db['SUBMITER_KEY'])
                    if results.has_key(submiter_field):
                        submiter_id = results.get(submiter_field)
                        if not submiter_id:
                            submiter_id = "''"
                        env_dbuser = ENVS[USERSDB]
                        dbuser_obj = lm.database(env_dbuser['HOST'], env_dbuser['USER'], env_dbuser['PASSWORD'], env_dbuser['DBNAME'])
                        results_user = dbuser_obj.execute('SELECT %s FROM %s WHERE (%s = %s) LIMIT 1;' % (
                            env_dbuser['NICK_FIELD'],
                            env_dbuser['USERS_TABLE'],
                            env_dbuser['USER_ID_FIELD'],
                            submiter_id) )
                        dbuser_obj.close()
                        if results_user and results_user[0].has_key(env_dbuser['NICK_FIELD']):
                            results[submiter_field] = results_user[0][env_dbuser['NICK_FIELD']]

                    # uncompress those compressed entries and add comments to the results_dic for display
                    tmpl = []
                    mol = ''
                    fields = fields_to_show_list_all['fields']
                    comments = fields_to_show_list_all['comments']
                    for j in xrange(len(fields)):
                        i = fields[j]
                        i = re.sub(r'^[^\.]+\.', '', i)
                        if i in [ dbd_obj.get_field(k) for k in env_db['COMPRESSED_KEYS'] ]:
                            # uncompress compressed entries
                            if i == dbd_obj.get_field(env_db['2D_STRUC_KEY']):
                                if session.removeh:
                                    mol = lm.mymol('mol', zlib.decompress(results[i])).removeh()
                                else:
                                    mol = zlib.decompress(results[i])
                            else:
                                tmpl.append([comments[j], zlib.decompress(results[i])])
                        else:
                            tmpl.append([comments[j], results[i]])
                    # show different interface to different groups
                    if db_name in EDITABLE_DBS and session.authorized and \
                            is_permited(session.userid, session.usergroup, ('u'), submiter_id):
                        results_dic['show_edit'] = True

                    results_dic['result_list'] = tmpl
                    results_dic['mol'] = mol
                    results_dic['mol_id'] = mol_id
                    results_dic['db'] = db_name
                    return html_molinfo(results_dic)
            else:
                return html_query_imcomplete(results_dic)
        except Exception, e:
            results_dic['info'].append('check your query')
            results_dic['info'].append(e)
            results_dic['html_title'] = 'query err'
            return html_info(results_dic)


    def __init__(self):
        # set the target language to session.lang
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'html_title': 'edit',
            'dbs': EDITABLE_DBS,
            'mol_id': None,
            'show_del': False,
            'current_page': 'edit',
            'calculable_keys': [],
            'submiter_nick': '',
            'needed_keys': [],
            'info': [],
            'lang': session.lang
            } )
    def GET(self, name = ''):
        input = web.input()
        results_dic = self.results_dic

        # check basic permission
        if ( not session.authorized ) or ( not is_permited(session.userid, session.usergroup, ('s', 'i')) ):
            return html_no_permision(results_dic)

        # chose which database to use
        if input.has_key('db') and input.get('db'):
            db_name = input.get('db')
            if ( db_name not in EDITABLE_DBS ) or ( not db_name in EDITABLE_DBS ):
                return html_wrong_db(results_dic)
            session.db = db_name
        else:
            db_name = EDITABLE_DBS[0]

        submiter_id = session.userid
        results_dic = self.results_dic
        needed_keys = []
        env_db = ENVS[db_name]
        dbd_obj = dbd_objs[db_name]
        sql_obj = lm.sql(env_db)
        pri_field = env_db['PRI_FIELD']
        tables = dbd_obj.tables

        # keys of the molecular properties that can be calculated (with out fingerprints keys)
        calculable_keys = lm.mymol.mol_data_keys() + lm.mymol.mol_stat_keys()

        for k in dbd_obj.comments_and_keys_list(
                [env_db['FP_TABLE']],
                [env_db['2D_STRUC_KEY'],
                env_db['SUBMITER_KEY']] + env_db['PRI_KEYS']):
            if not k[1] in calculable_keys:
                if not k[0]:
                    k[0] = k[1]
                needed_keys.append(k)

        # uniq needed_keys
        tmpl = []
        for i in needed_keys:
            if not i in tmpl:
                tmpl.append(i)
        needed_keys = tmpl

        # edit an exist molecule
        if input.has_key('mol_id'):
            mol_id = query_preprocessing(str(input.get('mol_id')))
            if not re.match('^[0-9]+$', mol_id):
                return html_query_illegal(results_dic)

            db_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])

            query_string = 'SELECT * FROM %s WHERE ( %s = %s ) LIMIT 1;' % (
                    sql_obj.gen_join_part_sql(tables, pri_field),
                    tables[0] + '.' + pri_field,
                    mol_id )
            results = db_obj.execute(query_string)
            db_obj.close()

            # check if the molecule exists and if the user has permission to edit it.
            if results:
                results = results[0]
                results_dic['mol_id'] = mol_id

                submiter_field = dbd_obj.get_field(env_db['SUBMITER_KEY'])
                if results.has_key(submiter_field):
                    submiter_id = results.get(submiter_field)

                # check the edit molecule permission (mast has 'u' in his permission list)
                if not is_permited(session.userid, session.usergroup, ('u'), submiter_id):
                    results_dic['info'] += ['can not edit mol', ': ' + mol_id]
                    results_dic['mol_id'] = ''
                else:
                    # congrats, you can edit the molecule, and we then prepare the mol info for display.

                    # if you can edit the molecule, then you can also delete it
                    results_dic['show_del'] = True

                    # change the decimal submiter id to nick name
                    env_dbuser = ENVS[USERSDB]
                    dbuser_obj = lm.database(env_dbuser['HOST'], env_dbuser['USER'], env_dbuser['PASSWORD'], env_dbuser['DBNAME'])
                    results_user = dbuser_obj.execute('SELECT %s FROM %s WHERE (%s = %s) LIMIT 1;' % (
                        env_dbuser['NICK_FIELD'],
                        env_dbuser['USERS_TABLE'],
                        env_dbuser['USER_ID_FIELD'],
                        submiter_id) )
                    dbuser_obj.close()
                    if results_user and results_user[0].has_key(env_dbuser['NICK_FIELD']):
                        results_dic['submiter_nick'] = results_user[0][env_dbuser['NICK_FIELD']]

                    # uncompress compressed entries
                    compressed_fields = [ dbd_obj.get_field(k) for k in env_db['COMPRESSED_KEYS'] ]
                    for i in compressed_fields:
                        if i == dbd_obj.get_field(env_db['2D_STRUC_KEY']):
                            if session.removeh:
                                mol = results[i] = lm.mymol('mol', zlib.decompress(results[i])).removeh()
                            else:
                                mol = results[i] = zlib.decompress(results[i])
                            results_dic['mol'] = mol
                        else:
                            results[i] = zlib.decompress(results[i])

                    # store the mol info into needed_keys
                    for i in needed_keys:
                        field = dbd_obj.get_field(i[1])
                        if field:
                            for k, v in results.items():
                                if field == k:
                                    i.append(v)
                                    continue
            else:
                # molecule with the id of the given mol_id dose not exist, change mode to "add mol"
                results_dic['info'] += ['no mol to show', ': ' + mol_id]
                results_dic['mol_id'] = ''

        results_dic['needed_tuple'] = needed_keys
        results_dic['db'] = db_name
        results_dic['db_selected'] = is_selected(db_name)
        return html_edit(results_dic)

    def POST(self, name = ''):
        input = web.input()
        values_dict = input.copy()
        results_dic = self.results_dic

        # check basic permission, 'i' permits add new molecule, while 'u' edit an exist molecule.
        if ( not session.authorized ) or ( not is_permited(session.userid, session.usergroup, ('s', 'i')) ):
            return html_no_permision(results_dic)

        # chose which database to use
        if input.has_key('db') and input.get('db'):
            db_name = input.get('db')
            session.db = db_name
        else:
            db_name = EDITABLE_DBS[0]
        if ( db_name not in EDITABLE_DBS ) or ( not db_name in EDITABLE_DBS ):
            return html_wrong_db(results_dic)

        env_db = ENVS[db_name]
        sql_obj = lm.sql(env_db)
        dbd_obj = dbd_objs[db_name]
        db_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])
        pri_field = env_db['PRI_FIELD']
        tables = dbd_obj.tables
        mol_id = ''
        smiles = ''
        add_mol = False
        submiter_id = session.userid
        submiter_field = dbd_obj.get_field(env_db['SUBMITER_KEY'])

        try:
            # smiles from the web input is needed
            if not (input.has_key('SMILES') and input.get('SMILES')):
                results_dic['info'].append('needed entry imcomplete')
                results_dic['html_title'] = 'needed entry imcomplete'
                return html_info(results_dic)
            else:
                smiles = query_preprocessing(str(input.get('SMILES')))

                if input.has_key('mol_id') and input.get('mol_id'):
                    mol_id = query_preprocessing(input.get('mol_id'))
                    if not re.match('^[0-9]+$', mol_id):
                        return html_query_illegal(results_dic)
                else:
                    try:
                        # the id of new added mol is the max id plus one.
                        mol_id = db_obj.execute('SELECT max(%s) AS max_mol_id FROM %s;' %(pri_field, tables[0]))[0]['max_mol_id']
                        mol_id = str(int(mol_id) + 1)
                        # add new molecule. those has permission of executing 'i' action can do this.
                        add_mol = True
                    except:
                        pass

                if not (mol_id and smiles):
                    results_dic['info'].append('needed entry imcomplete')
                    results_dic['html_title'] = 'needed entry imcomplete'
                    return html_info(results_dic)
                else:
                    # check if one has the permission to edit the molecule ( user not in group 1 can only
                    # insert new ones or update those submited by himself)
                    if not add_mol:
                        # if you are here, then you are editing an exist molecule, only those
                        # has the permission of executing 'u' action can do this.

                        # find the submiter of the molecule with the id of mol_id
                        query_string = 'SELECT %s FROM %s WHERE ( %s = %s ) LIMIT 1;' % (
                                submiter_field,
                                dbd_obj.get_table_name(env_db['SUBMITER_KEY']),
                                pri_field,
                                mol_id )
                        results = db_obj.execute(query_string)
                        if results:
                            results = results[0]
                            if results.has_key(submiter_field):
                                submiter_id = results.get(submiter_field)

                        # check the edit exist molecule permission
                        if not is_permited(session.userid, session.usergroup, ('u'), submiter_id):
                            results_dic['html_title'] = 'permission denied'
                            results_dic['info'] += ['<br/>', 'can not edit mol', ': ' + mol_id]
                            return html_info(results_dic)

                    for id_key in env_db['PRI_KEYS']:
                        values_dict[id_key] = mol_id

                    # the submiter id should keep still

                    # caculates the caculable properties
                    tmp_dict = {}
                    mol = lm.mymol('smi', smiles)
                    mol.get_mol_data(tmp_dict)
                    mol.get_fps(tmp_dict)
                    mol.get_mol_stat(tmp_dict)
                    values_dict.update(tmp_dict)

                    # store the new info of the mol
                    for sql_string in sql_obj.gen_insert_sqls(values_dict, 'REPLACE').values():
                       db_obj.execute(sql_string + ';')
                    db_obj.close()

                    results_dic['html_title'] = 'edit finished'
                    results_dic['info'] += ['edit mol finished',
                            '<a href="%s?db=%s&mol_id=%s">%s</a>' %(URLS_DIC['molinfo_url'], db_name, mol_id, mol_id)]
                    return html_info(results_dic)
        except Exception, e:
            results_dic['info'].append('check your query')
            results_dic['info'].append(e)
            results_dic['html_title'] = 'query err'
            return html_info(results_dic)

class delmol:
    '''
    this class deletes the molecule from the database
    '''
    def __init__(self):
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'html_title': 'del mol',
            'info': [],
            'current_page': 'search',
            'lang': session.lang
            } )
    def GET(self, name = ''):
        input = web.input()
        results_dic = self.results_dic
        available_dbs = PUBLIC_DBS
        if session.authorized:
            available_dbs = DATABASES
            self.results_dic.update({'dbs': available_dbs})

        # check basic permission
        if ( not session.authorized ) or ( not is_permited(session.userid, session.usergroup, ('s', 'i')) ):
            return html_no_permision(results_dic)

        # chose which database to use
        if input.has_key('db') and input.get('db'):
            db_name = input.get('db')
            if ( db_name not in available_dbs ) or ( not db_name in EDITABLE_DBS ):
                return html_wrong_db(results_dic)
            session.db = db_name
        else:
            db_name = session.db

        env_db = ENVS[db_name]
        sql_obj = lm.sql(env_db)
        dbd_obj = dbd_objs[db_name]
        pri_field = env_db['PRI_FIELD']
        tables = dbd_obj.tables
        submiter_id = session.userid
        submiter_field = dbd_obj.get_field(env_db['SUBMITER_KEY'])
        empty_mol_list = []
        del_failed_mol_list = []
        del_finished_mol_list = []

        if input.has_key('mol_id') and input.get('mol_id'):
            mol_id_list = [ id for id in query_preprocessing(input.get('mol_id')).split('|') if id ]
            for id in mol_id_list:
                if not re.match('^[0-9]+$', id):
                    return html_query_illegal(results_dic)

            db_obj = lm.database(env_db['HOST'], env_db['USER'], env_db['PASSWORD'], env_db['DBNAME'])

            for mol_id in mol_id_list:
                submiter_id = ''
                # find the submiter of the molecule with the id of mol_id
                query_string = 'SELECT %s FROM %s WHERE ( %s = %s ) LIMIT 1;' % (
                        submiter_field,
                        dbd_obj.get_table_name(env_db['SUBMITER_KEY']),
                        pri_field,
                        mol_id )
                results = db_obj.execute(query_string)
                if results:
                    results = results[0]
                    if results.has_key(submiter_field):
                        submiter_id = results.get(submiter_field)
                else:
                    empty_mol_list.append(mol_id)
                    continue

                # check if you can delete a molecule
                if not is_permited(session.userid, session.usergroup, ('u'), submiter_id):
                    del_failed_mol_list.append(mol_id)
                    continue
                else:
                    for t in tables:
                        db_obj.execute("DELETE FROM %s WHERE (%s = %s);" %(t, pri_field, mol_id))
                    del_finished_mol_list.append(mol_id)
            db_obj.close()

            results_dic['html_title'] = 'del report'
            if del_failed_mol_list:
                # report the deleting failed molecules
                mol_url_list = []
                for id in del_failed_mol_list:
                    mol_url_list.append('<br/><a href="%s?db=%s&mol_id=%s">%s</a>' %(URLS_DIC['molinfo_url'], db_name, id, id))
                results_dic['info'] += ['del mol failed', ':', '\n'.join(mol_url_list)]
            if empty_mol_list:
                for id in empty_mol_list:
                    results_dic['info'] += ['<br/>', 'empty mol entry', '<br/>' + id]
            if del_finished_mol_list:
                mol_url_list = []
                for id in del_finished_mol_list:
                    results_dic['info'] += ['<br/>', 'del mol', id, 'completed']
            return html_info(results_dic)
        else:
            results_dic['info'].append('mol id not post')
            results_dic['html_title'] = 'needed entry imcomplete'
            return html_info(results_dic)

class mymols:
    def __init__(self):
        trans_class.lang = session.lang
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'info': [],
            'lang': session.lang
            } )
    def GET(self, name = ''):
        input = web.input()
        results_dic = self.results_dic
        available_dbs = PUBLIC_DBS
        if session.authorized:
            available_dbs = DATABASES
            self.results_dic.update({'dbs': available_dbs})

        # check basic permission
        if ( not session.authorized ) or ( not is_permited(session.userid, session.usergroup, ('s', 'i')) ):
            return html_no_permision(results_dic)

        # chose which database to use
        if input.has_key('db') and input.get('db'):
            db_name = input.get('db')
            if db_name not in available_dbs:
                return html_wrong_db(results_dic)
            session.db = db_name
        else:
            db_name = session.db

        env_db = ENVS[db_name]
        submiter_abbr = env_db['SUBMITER_ABBR']

        return web.seeother('%s?mode=%s&db=%s&prequery=%s' %(
            URLS_DIC['search_url'], '4', db_name, submiter_abbr + '+%3D+' + str(session.userid)))

class doc:
    def __init__(self):
        # set the target language to session.lang
        trans_class.lang = session.lang
        # docments
        self.results_dic = tpl_results_dic.copy()
        self.results_dic.update( {
            'logged_user': session.nickname,
            'trans_class': trans_class,
            'html_title': 'mol info',
            'info': [],
            'current_page': 'help',
            'lang': session.lang
            } )
        def doc_render(lang, tpl_name, **kwargs):
            return DOC_RENDER(lang, tpl_name, **kwargs)
        self.doc_render = doc_render
    def GET(self, name = ''):
        input = web.input()
        results_dic = self.results_dic
        results_dic['html_title'] = 'help'
        info_head = ''
        doc_id = ''

        # check basic permission
        if not is_permited(session.userid, session.usergroup, ('s')):
            return html_no_permision(results_dic)

        if input.has_key('doc_id') and input.get('doc_id'):
            doc_id = input.get('doc_id')
            if doc_id == 'about':
                results_dic['current_page'] = 'about'
                results_dic['html_title'] = 'about'

            f = DOCUMENTS_PATH + '/' + session.lang + '/' + '.html'
            if not os.path.exists(f):
                f = DOCUMENTS_PATH + '/' + DEFAULT_LANG + '/' + doc_id + '.html'
            if os.path.exists(f):
                info_head = doc_id
                tmp_line = open(f).readline().rstrip('\n')
                if re.findall(r'^ *##', tmp_line):
                    info_head = re.sub(r'^ *##', '', tmp_line)
                results_dic['info_head'] = info_head
            else:
                results_dic['info'].append('failed to open document')
                results_dic['html_title'] = 'query err'
                return html_info(results_dic)

            try:
                return WEB_RENDER('header', results_dic = results_dic) + \
                        WEB_RENDER('info', results_dic = results_dic) + \
                        self.doc_render(session.lang, doc_id) + \
                        WEB_RENDER('footer', results_dic = results_dic)
            except SyntaxError:
                results_dic['info'].append('failed to open document')
                results_dic['html_title'] = 'query err'
                return html_info(results_dic)
            except:
                try:
                    return WEB_RENDER('header', results_dic = results_dic) + \
                            WEB_RENDER('info', results_dic = results_dic) + \
                            self.doc_render(DEFAULT_LANG, doc_id) + \
                            WEB_RENDER('footer', results_dic = results_dic)
                except AttributeError:
                    results_dic['info'].append('check your query')
                    results_dic['html_title'] = 'query err'
                    return html_info(results_dic)
        else:
                results_dic['info_head'] = 'documents'
                help_urls = []
                title = ''
                for i in os.listdir(DOCUMENTS_PATH + '/' + session.lang):
                    try:
                        f = DOCUMENTS_PATH + '/' + session.lang + '/' + i
                        title = re.sub('.html$', '', i)
                        tmp_line = open(f).readline().rstrip('\n')
                        if re.findall(r'^ *##', tmp_line):
                            title = re.sub(r'^ *##', '', tmp_line)
                        help_urls.append((title, URLS_DIC['doc_url'] + '?doc_id=' + re.sub('.html$', '', i)))
                    except:
                        pass
                return WEB_RENDER('header', results_dic = results_dic) + \
                        WEB_RENDER('info', results_dic = results_dic) + \
                        WEB_RENDER('doc_links', links = help_urls) + \
                        WEB_RENDER('footer', results_dic = results_dic)

class chsettings:
    '''change setting such as language, search mode and database'''
    def GET(self, name = ''):
        input = web.input()
        info = ''

        if input.has_key('lang') and input.get('lang'):
            lang = input.get('lang')
            if lang in LANGS:
                session.lang = lang
                info += 'change language OK.\n'
        if input.has_key('mode') and input.get('mode'):
            mode = input.get('mode')
            if mode in SEARCH_MODES:
                session.search_mode = mode
                info += 'change mode OK.\n'
        if input.has_key('db') and input.get('db'):
            db = input.get('db')
            if db in available_dbs:
                session.db = db
                info += 'change database OK.\n'
        return info

# run site
if __name__ == "__main__":
    app.run()
