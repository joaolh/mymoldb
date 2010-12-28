#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     db.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  100305

import re, MySQLdb, MySQLdb.cursors

class database():
    def __init__(self, host, user, passwd, db, curcls = MySQLdb.cursors.DictCursor):
        self.conn = MySQLdb.connect(host, user, passwd, db, charset='utf8')
        self.cursor = self.conn.cursor(cursorclass = curcls)
    def cursor(self):
        return self.cursor
    def execute(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def query(self, sql, filter = None, dot_pri_field = None, limit = 300, num_per_select = 150):
        '''limit < 0 means no results limitation'''
        results = []
        results_tmp = []
        limit_left = 0
        last_pri_field = ''
        pri_field = re.sub(r'^[^\.]+\.', '', dot_pri_field)
        if not filter:
            num_per_select = limit

        limit_part = ''
        if limit >= 0:
            limit_part = ' LIMIT ' + str(num_per_select)

        while ( lambda limit, results: limit < 0 and True or len(results) < limit )(limit, results):
            if pri_field and results_tmp:
                if results_tmp[-1].has_key(pri_field):
                    if last_pri_field == str(results_tmp[-1][pri_field]):
                        break
                    else:
                        last_pri_field = str(results_tmp[-1][pri_field])
                else:
                    last_pri_field = '0'

                if re.findall(r'\b[Ww][Hh][Ee][Rr][Ee]\b', sql):
                    sql_string = sql + ' AND (' + dot_pri_field + ' > ' + last_pri_field + ')' + limit_part + ';'
                else:
                    sql_string = sql + ' WHERE (' + dot_pri_field + ' > ' + last_pri_field + ')' + limit_part + ';'
            else:
                sql_string = sql + ' LIMIT ' + str(limit_left) + ',' + str(num_per_select) + ';'
                limit_left += num_per_select

            self.cursor.execute(sql_string)
            results_tmp = list(self.cursor.fetchall())
            if not results_tmp:
                break
            if filter: # filter can be a function takes a result dict as its argument
                results += [ i for i in results_tmp if filter(i) ]
            else:
                results += results_tmp
        return results
    def close(self):
        self.conn.close()

class users_db():
    def __init__(self, env_db):
        self.env_db = env_db
        self.userdb_obj = database(self.env_db['HOST'], self.env_db['USER'], self.env_db['PASSWORD'], self.env_db['DBNAME'])
    def select(self, fields, where_part):
        env_db = self.env_db
        userdb_obj = self.userdb_obj
        fields_string = ','.join(fields)
        table = env_db['USERS_TABLE']
        return userdb_obj.execute('SELECT %s FROM %s WHERE %s;' %(fields_string, table, where_part))
    def update_usersdb(self, fields_and_values_dic, where_part):
        env_db = self.env_db
        userdb_obj = self.userdb_obj
        table = env_db['USERS_TABLE']
        set_part = ''
        for f, v in fields_and_values_dic.items():
            set_part += f + " = '" + v + "', "
        userdb_obj.execute('UPDATE %s SET %s WHERE %s;' %(table, set_part.rstrip(', '), where_part))

    def insert_into_usersdb(self, id, nick, usergroup, md5_pw, username, regtime, status):
        env_db = self.env_db
        userdb_obj = self.userdb_obj
        userdb_obj.execute('INSERT INTO %s(%s) VALUES(%s);' %(
            env_db['USERS_TABLE'],
            "%s, %s, %s, %s, %s, %s, %s" %(
                env_db['USER_ID_FIELD'],
                env_db['NICK_FIELD'],
                env_db['USER_GROUP_FIELD'],
                env_db['PASSWORD_FIELD'],
                env_db['USER_EMAIL_FIELD'],
                env_db['RGI_DATE_FIELD'],
                env_db['STATUS_FIELD']),
            "'%s', '%s', '%s', '%s', '%s', '%s', '%s'" %(
                id, nick, usergroup, md5_pw, username, regtime, status)))
    def delete(self, where_part):
        env_db = self.env_db
        userdb_obj = self.userdb_obj
        userdb_obj.execute('DELETE FROM %s WHERE %s;' %(env_db['USERS_TABLE'], where_part))
    def close(self):
        self.userdb_obj.close()
