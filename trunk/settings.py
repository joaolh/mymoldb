#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     settings.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  091217

'''settings for main.py'''

import web, time, os, re
from mako.template import Template
from mako.lookup import TemplateLookup
from libmymoldb import dbdef, sql_fields

# paths
TRANS_PATH = "trans"
CACHE_PATH = "cache"
TEMPLATES_PATHS = ['templates']
DOCUMENTS_PATH = 'documents'
MAKO_MODULES_PATH = '/tmp/mako_modules'

# init mako renders
mylookup = lambda tpl_dirs, module_dir: TemplateLookup(directories = tpl_dirs,
        module_directory = module_dir,
        input_encoding='utf-8',
        output_encoding='utf-8')
def WEB_RENDER(tpl_name, **kwargs):
    tpl_name = re.findall(r'\.html$', tpl_name) and tpl_name or tpl_name + '.html'
    return mylookup(TEMPLATES_PATHS, MAKO_MODULES_PATH + '/web').get_template(tpl_name).render(**kwargs)
def DOC_RENDER(lang, tpl_name, **kwargs):
    tpl_name = re.findall(r'\.html$', tpl_name) and tpl_name or tpl_name + '.html'
    return mylookup([DOCUMENTS_PATH + '/' + lang], MAKO_MODULES_PATH + '/doc/' + lang).get_template(tpl_name).render(**kwargs)


# sendmail configuration
SENDMAIL_SETTINGS_DICT = {
        'smtp': 'smtp.xxx.com', # smtp server
        'from': '"MyMolDB administrator"',
        'user': 'xxx', # the smtp user
        'passwd': 'xxx' # the smtp pass word
        }

# should the admin manually approve the register?
APPROVE_ALL_REGISTERS = False
# file to store the register info
REGISTER_INFO_FILE = CACHE_PATH + '/' + 'register_info_file.pkl'

# the default user group, permisions of each group see ACTIONS_RULES
DEFAULT_USER_GROUP = 2
# available user groups
USER_GROUPS = (1, 2, 3)
# for authority control
# actions in the action tuples are allowed to execute
ACTIONS_RULES = {
        # user group: ( actions )
        # 's' means select, 'i' insert, 'u', update, replace or remove
        # those actions are mysql actions needed in the next steps
        1: ('s', 'i', 'u'),
        2: ('s', 'i'),
        3: ('s')
        }

# available languages
LANGS = [ i.rstrip('.txt') for i in os.listdir(TRANS_PATH) if i.endswith('.txt') ]
# default language
DEFAULT_LANG = 'en_US'

# web config. set cookies aspects
web.config.values()[2]["cookie_name"] = "mymoldb_session_id"
web.config.values()[2]["timeout"] = 3600
web.config.values()[2]["ignore_change_ip"] = False

# url map for main.py
URL_MAP = (
        # url, class
        '/db/user/login', 'login',
        '/db/user/logout', 'logout',
        '/db/user/ucpanel', 'ucpanel',
        '/db/user/register', 'register',
        '/db/user/man_users', 'man_users',
        '/db/user/chusersettings', 'chusersettings',
        '/db/user/mymols', 'mymols',
        '/db/search', 'search',
        '/db/webapi', 'webapi',
        '/db/molinfo', 'molinfo',
        '/db/chsettings', 'chsettings',
        '/db/edit', 'edit',
        '/db/delmol', 'delmol',
        '/db/doc', 'doc',
        '/db/(.*)', 'index'
        )

# urls dict for url replacement in the templates
URLS_DIC = {
        # key: url
        'home_url': '/db/',
        'login_url': '/db/user/login',
        'logout_url': '/db/user/login?action=logout',
        'ucpanel_url': '/db/user/ucpanel',
        'register_url': '/db/user/register',
        'manusers_url': '/db/user/man_users',
        'chusersetting_url': '/db/user/chusersettings',
        'mymols_url': '/db/user/mymols',
        'search_url': '/db/search',
        'webapi_url': '/db/webapi',
        'molinfo_url': '/db/molinfo',
        'trans_url': '/db/chsettings',
        'chmode_url': '/db/chsettings',
        'chdb_url': '/db/chsettings',
        'editmol_url': '/db/edit',
        'delmol_url': '/db/delmol',
        'doc_url': '/db/doc',
        'js_dir': '/js',
        'css_dir': '/css'
}
# navigation links of the site
NAV_LINKS = (
        #(name, url)
        ('home', '/db/index'),
        ('search', URLS_DIC['search_url']),
        ('edit', URLS_DIC['editmol_url']),
        ('help', '/db/doc'),
        ('about', '/db/doc?doc_id=about')
        )

# user control panel urls
UCP_URLS = (
        #(name, url, target)
        # if target is not set, then the page will be embeded into an iframe by default
        ('change settings', URLS_DIC['chusersetting_url'], ''),
        ('mymols', URLS_DIC['mymols_url'], '_blank')
        )

# time out of the results file, in seconds
RESULTS_FILE_TIME_OUT = 604800, # a week
LOCK_FILE_LIFE_SPAN = 600, # 10 min

# databases, details can be seen in the ENVS dict
USERSDB = 'users'
DATABASES = ('1',)
EDITABLE_DBS = ('1',)
PUBLIC_DBS = ('1',)

# avalable search modes
# 1 means full match, 2 means substructure search, 3 means similarity search,
# while 4 is advanced mode. these modes are different from those search types
# in the libmymoldb.sql class
SEARCH_MODES = ('1', '2', '3', '4', '5')

MAX_LOGIN_TRY_TIMES = 5
LOGIN_INTERVAL = 60 # in seconds

# session part
def SESSION(app):
    return web.session.Session(
        app,
        web.session.DiskStore('sessions'),
        # if authorized, set value of this key 'yes'. usertypes are
        # viewer, commiter, admin, advansed-user
        initializer={
            # authority control part
            # username should be email
            'username': '',
            'userid': '',
            'nickname': '',
            'authorized': False,
            'usergroup': 3,
            # for login control
            'login_try_times': 0,
            'last_login_time': time.time(),
            # default language
            'lang': DEFAULT_LANG,
            # max results number to find when sql querying
            'max_results_num': 300,
            # default results to show per page
            'results_per_page': 10,
            # the mol file to search
            'search_mol': '',
            # remove the extra H elements or not when displaying the molecules
            'removeh': True,
            # md5 hash of the search query
            'md5_query': '',
            # the search mode, 1 means full match, 2 means substructure search,
            # 3 means similarity search, while 4 is advanced mode.
            'search_mode': "2",
            # more than one molecules may be queried in the advanced search mode
            'query_smiles_dic': {},
            'query_mols_dic': {},
            # default database to use
            'db': '1',
            }
        )

ENVS = {
        # envs for database which stores info of users
        'users': {
            'HOST': 'localhost',
            # set your database user
            'USER': 'database_user',
            # set your database password
            'PASSWORD': 'database_password',
            'DBNAME': 'users',
            'USERS_TABLE': 'mymoldb_users',
            'USER_ID_FIELD': 'id',
            'USER_EMAIL_FIELD': 'email',
            'NICK_FIELD': 'nick_name',
            'RGI_DATE_FIELD': 'register_date',
            'STATUS_FIELD': 'status',
            'PASSWORD_FIELD': 'password',
            'USER_GROUP_FIELD': 'user_group'
            },
        # envs for example database nomber 1, the pubchem database
        '1': {
            'HOST': 'localhost',
            # set your database user
            'USER': 'database_user',
            # set your database password
            'PASSWORD': 'database_password',
            'DBNAME': 'pubchem',
            'DEF_FILE': 'defs/db_pubchem.def',
            'SUBMITER_KEY': 'SUBMITER_ID', # key is the first field in the def file
            'PRI_FIELD': 'mol_id',
            # SIMI_FIELD can be any name you like, for it's not real column in database
            'SIMI_FIELD': 'simi_value',
            'FIELDS_TO_SHOW_FILE': 'fields_to_show_files/pubchem.txt',
            'SMILES_KEY': 'OPENBABEL_CAN_SMILES',
            'MD5_OPENBABEL_CAN_SMI_KEY': 'MD5_OPENBABEL_CAN_SMILES',
            'FP_TABLE': 'mol_fp',
            'FP_BITS_KEY': 'FP_BITS',
            'NUM_H_KEY': 'NUM_H',
            '2D_STRUC_KEY': 'MOL_2D_STRUC',
            '2D_STRUC_FIELD': 'mol_2d_struc',
            'SUBMITER_ABBR': 'sid',
            }
        }

# compute some useful things and update ENVS
for k, v in ENVS.items():
    if v.has_key('DEF_FILE'):
        tmp_dic = {}
        dbd_obj = dbdef(v['DEF_FILE'])
        tmp_dic = {
                'COMPRESSED_KEYS': dbd_obj.get_pic_key_list('COMPRESS'),
                'PRI_KEYS': dbd_obj.get_pic_key_list('PRIMARY'),
                # abbreviated sql fields (for advanced search)
                'ABBR_DIC': dbd_obj.get_abbr_dic()
                }
        if v.has_key('FIELDS_TO_SHOW_FILE'):
            sf_dic = {}
            sql_fields_obj = sql_fields(v['DEF_FILE'])
            for i in ('all', 'part'):
                sf_dic[i] = sql_fields_obj.get_fields(v['FIELDS_TO_SHOW_FILE'], i)
            tmp_dic['FIELDS_TO_SHOW_DIC'] = sf_dic
    if tmp_dic:
        ENVS[k].update(tmp_dic)

if __name__ == '__main__':
    print ENVS
