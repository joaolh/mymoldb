#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     dbdef.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  100305

class dbdef():
    def __init__(self, def_file):
        '''
        args:
            def_file: str, the def file name. format of the def file should be:
                    >>>TABLE_NAME:table_name:table args
                   key:MySQL_field_name:MySQL_field_type:comment:PRIMARY/INDEX or not:default value
        '''
        self.def_file = def_file
        self.def_dict, self.table_args, self.ordered_fields_dict = self._get_def_dict()
        self.tables = self.def_dict.keys()
    def _get_def_dict(self):
        '''
        get_def_dict() -- Returns a tuple.

        get the recorded fields from the given def file.
        retult looks like this:
        0: { table_name: {key: [MySQL_field_name, comment, ...]}, ... }
        1: { table_name: table_args, ... }
        2: { table_name: [ {key: [MySQL_field_name, comment, ...]}, ...], ...}
        '''
        tmp_dic = {}
        tmpl = []
        result0 = {}
        result1 = {}
        result2 = {}
        table_name = ''
        table_args = ''
        read = True
        f = open(self.def_file)
        while read:
            line = f.readline()
            if ( not line.startswith("#") ) and ( not line.startswith(">>>") ):
                l = line.rstrip('\n').split(":")
                if len(l) > 2:
                    tmp_dic[l[0]] = l[1:]
                    tmpl.append({l[0]: l[1:]})
            elif line.startswith(">>>"):
                if tmp_dic and table_name:
                    result0[table_name] = tmp_dic
                    tmp_dic = {}
                    tmpl = []
                table_name, table_args = line.split(':')[1:3]
                result1[table_name] = table_args.rstrip('\n')
                result2[table_name] = tmpl
            if not line:
                read = False
                if table_name:
                    result0[table_name] = tmp_dic
        return result0, result1, result2

    def recorded_fields_dict(self, exclude = []):
        '''
        recorded_fields_dict([exclude]) -- Returns a dict.

        args:
            exclude: list, don't record those field names key) inside.

        get the recorded keys from the given def file, the format of the result
        looks like this:
        { key: MySQL_field_name, ...}
        '''
        result = {}
        l = []
        for v in self.def_dict.values():
            for k0, v0 in v.items():
                result[k0] = v0[0]
        return result

    def comments_and_keys_list(self, exclude_tables = [], exclude_keys = []):
        '''
        comments_and_keys_list([exclude_tables[, exclude_keys]]) -- Returns a list.

        args:
         exclude_tables: list, the tables that you don't want to record.
         exclude_keys: list, the keys that you don't want to record.

         returns a list contains lists with 2 elements: comment and key
        '''
        result = []
        for k, v in self.def_dict.items():
            if not k in exclude_tables:
                for k0, v0 in v.items():
                    if not k0 in exclude_keys:
                        result.append([v0[2], k0])
        result.sort(key = lambda x: x[0])
        return result

    def get_comment(self, key):
        '''
        get_comment(key) -- Returns a string.

        args:
            key: string, the key of the sql field.
        '''
        defs_dict = self.key_defs_dict(key)
        if defs_dict.has_key('COMMENT'):
            return defs_dict['COMMENT']
        return ''

    def get_pic_key_list(self, type):
        '''
        get_pic_key_list() -- Returns a list.

        args:
            type: string, the PIC (Primary, Index and Compress) type: PRIMARY, INDEX or COMPRESS

        '''
        l = []
        for v in self.ordered_fields_dict.values():
            for d in v:
                for i in d.values()[0]:
                    if i.startswith(type):
                        l.append(d.keys()[0])
        return l


    def get_table_name(self, key):
        '''
        get_table_name(key) -- Returns a string.

        args:
            key: string, the key of the sql field.

        returns the table which contains the key
        '''
        for k, v in self.def_dict.items():
            if key in v.keys():
                return k
        return ''

    def get_field(self, key):
        '''
        get_fields(key) -- Returns a string.

        args:
            key: string, the key of the sql field.

        returns the field of the given key
        '''
        defs_dict = self.key_defs_dict(key)
        if defs_dict.has_key('MYSQL_FIELD'):
            return defs_dict['MYSQL_FIELD']
        return ''

    def key_defs_dict(self, key):
        '''
        key_defs_dict(key) -- Returns a dict.

        args:
            key: string, the key of the sql field.

        returns the definations of a key in a dict
        '''
        result = {}
        defs = []
        mysql_field = ''
        result['TABLE'] = self.get_table_name(key)
        if not result['TABLE']:
            return {}
        if self.def_dict[result['TABLE']].has_key(key):
            defs = self.def_dict[result['TABLE']][key]
        else:
            return {}
        # pri field should add the table name
        if defs[3].startswith('PRIMARY'):
            mysql_field = result['TABLE'] + '.' + defs[0]
        else:
            mysql_field = defs[0]
        result.update( {
            'KEY': key,
            'MYSQL_FIELD': mysql_field,
            'MYSQL_FIELD_TYPE': defs[1],
            'COMMENT': defs[2],
            # Primary, Index or Compress flag
            'PIC': defs[3],
            'DEFAULT_VALUE': defs[4]
            } )
        return result
    def get_abbr_dic(self):
        '''
        get_abbr_dic() -- Returns a dict.

        returns a dict of the abbreviated key and the coordinate MySQL_field_name
        '''
        abbr_dic = {}
        for k, v in self.def_dict.items():
            for v0 in v.values():
                if v0[5]:
                    if v0[3] == 'PRIMARY':
                        val = k + '.' + v0[0]
                    else:
                        val = v0[0]
                    abbr_dic[v0[5]] = val
        return abbr_dic
