#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     sql.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  100305

import zlib, re, sys
from dbdef import dbdef
from mol import mymol
from functions import md5

class sql_fields():
    def __init__(self, dbdef_file):
        self.dbdef = dbdef(dbdef_file)
    def get_fields(self, def_file, arg = 'all'):
        '''
        fields_to_show([arg]) -- Returns a dict with two lists which
        can be accessed via the key 'fields' and 'comments'.

        args:
            arg: str, could be 'all' or 'part'.

        generates the fields to show list from the def file, fields could be
        all (all fields) or part (part of the fileds for summary).
        '''
        l_fields = []
        l_comments = []
        tmpl = []
        append = False
        if arg == 'all':
            for i in open(def_file):
                if i.startswith('#=='):
                    append = True
                if append and ( not i.startswith('#') ):
                    tmpl = i.strip('\n').split(':', 1)
                    if len(tmpl) == 2:
                        l_fields.append(self.dbdef.get_field(tmpl[0]))
                        l_comments.append(tmpl[1])
                    else:
                        l_fields.append(self.dbdef.get_field(tmpl[0]))
                        l_comments.append(self.dbdef.get_comment(tmpl[0]))
        elif arg == 'part':
            for i in open(def_file):
                if not ( i.startswith('#==') or i.startswith('#') ):
                    tmpl = i.strip('\n').split(':', 1)
                    if len(tmpl) == 2:
                        l_fields.append(self.dbdef.get_field(tmpl[0]))
                        l_comments.append(tmpl[1])
                    else:
                        l_fields.append(self.dbdef.get_field(tmpl[0]))
                        l_comments.append(self.dbdef.get_comment(tmpl[0]))
                elif i.startswith('#=='):
                    break
        return {'fields': l_fields, 'comments': l_comments}

class sql():
    def __init__(self, env):
        '''
        the sql class for sql string generating.

        args:
            env: dict, shoule contains keys as follows:
                Needed keys:
                'DEF_FILE': the keys_to_sql_fields define file (eg. sdf2sql.def)
                'MD5_OPENBABEL_CAN_SMI_KEY': the key of the md5_openbabel_can_smiles field
                'FP_BITS_KEY': the key of the fp_bits (fingerprints bits) field
                'SIMI_FIELD': the name of the similarity value shows out in the similarity search part
                'PRI_FIELD': the name of the primary field

                Optional ones:
                'NUM_H_KEY': the key of the NUM_H (number of element H) field
        '''

        self.env = env
        self.dbd = dbdef(self.env['DEF_FILE'])
        self.recorded_fields_dict = self.dbd.recorded_fields_dict()
        self.def_dict = self.dbd.def_dict
    @classmethod
    def gen_join_part_sql(self, tables, pri_field):
        '''
        gen_join_part_sql(tables, pri_field) --Returns a string.

        args:
            tables: list/tuple, tables to join.
            pri_field: string, the primary field of the table, all the names of the primary key of the tables
                should be the same.

        returns a sql string from the tables.
        '''
        s = ''
        i = 0
        j = 0
        for i in range(len(tables)):
            j = i + 1
            if j <= len(tables) - 1:
                if i == 0:
                    s += '%s INNER JOIN %s ON (%s = %s) ' % (
                            tables[i],
                            tables[j],
                            tables[i] + '.' + pri_field,
                            tables[j] + '.' + pri_field )
                else:
                    s += 'INNER JOIN %s ON (%s = %s) ' % (
                            tables[j],
                            tables[i] + '.' + pri_field,
                            tables[j] + '.' + pri_field )
            else:
                return s
    def gen_search_sql_tuple(self, smiles, search_type = "1", out_put_type = 1):
        '''
        gen_search_sql_tuple(smiles[, search_type[, out_put_type]]) -- Returns a tuple

        args:
            smiles: str, smiles that represents a molecule.
            search_type: str. values:
                '1': full march,
                '2': target structure contains substructure,
                '3': target structure dosen't contains substructure
                '4': target structure contains superstructure,
                '5': target structure dosen't contains superstructure
            out_put_type: int. values:
                1 or not 2: without the mol_stat part.
                2: contains the mol_stat part

        generates the search sql string according to the smiles string.
        returns a tuple contains two elements:
            0: stat, some statistic of the mol such as number of C, number of rings and etc.
            1: the sql part, sql not fully generated, only a part like this " FROM ... WHERE ... "
        '''
        fp_sql = ""
        stat = {}
        head_flag = '('
        end_flag = ')'
        stat_part = ''
        md5_ob_can_smi_key = self.env['MD5_OPENBABEL_CAN_SMI_KEY']
        fp_bits_key = self.env['FP_BITS_KEY']
        sign_mol_stat = ' >= '
        try:
            num_H_key = self.env['NUM_H_KEY']
        except:
            num_H_key = 'NUM_H'
        bool_op = " AND "
        mol_fp = {}
        mol = mymol('smi', smiles)
        mol.get_fps(mol_fp)
        if search_type == "1":
            if md5_ob_can_smi_key in self.recorded_fields_dict.keys():
                return ({}, self.recorded_fields_dict[md5_ob_can_smi_key] + " = '" + md5(mymol('smi', smiles).gen_openbabel_can_smiles()) + "'")
            else:
                return ({}, '')
        elif search_type in ("2", "4"):
            mol_stat = {}
            tmp_stat = {}
            mol.get_mol_stat(mol_stat)
            if mol_stat.has_key(num_H_key):
                mol_stat.pop(num_H_key)
            tmp_stat[str(fp_bits_key)] = mol_fp[fp_bits_key]
            tmp_stat.update(mol_stat)
            if search_type == '2':
                sign_mol_stat = ' >= '
                stat['sub'] = tmp_stat
            elif search_type == '4':
                sign_mol_stat = ' <= '
                stat['sup'] = tmp_stat
            bool_op = ' AND '
        elif search_type in ("3", "5"):
            bool_op = ' AND '
            head_flag = ' NOT ('
        fps_keys = mol_fp.items()
        fps_keys.sort()
        for i, j in fps_keys:
            if self.recorded_fields_dict.has_key(i) and i != fp_bits_key and j != 0:
                if search_type in ('2', '3'):
                    fp_sql += self.recorded_fields_dict[i] + " & " + str(j) + ' = ' + str(j) + bool_op
                elif search_type in ('4', '5'):
                    field = self.recorded_fields_dict[i]
                    fp_sql += field + " & " + str(j) + ' = ' + field + bool_op
        if out_put_type == 2 and search_type in ('2', '4'):
            val_k = []
            for k, v in tmp_stat.items():
                for j in self.def_dict.values():
                    if j.has_key(k):
                        val_k = j[k][0]
                        break
                if val_k:
                    stat_part += str(val_k) + sign_mol_stat + str(v) + ' AND '
            if stat_part:
                head_flag = '(' + stat_part.rstrip('AND ') + ') AND ('
        if fp_sql.rstrip(bool_op):
            return (stat, head_flag + fp_sql.rstrip(bool_op) + end_flag)
        else:
            return ({}, '1')
    def gen_search_sql(self, smiles, search_type = "1"):
        '''
        gen_search_sql(smiles[, search_type]) -- Returns a string.

        args:
            smiles: str, smiles that represents a molecule.
            search_type: str. values:
                '1': full march,
                '2': target structure contains substructure,
                '3': target structure dosen't contains substructure

        returns a partial sql string like ' FROM ... WHERE ... '
        '''
        join_part_sql = self.gen_join_part_sql(self.dbd.tables, self.env['PRI_FIELD'])
        return ' FROM %s WHERE (%s) ' %(join_part_sql, self.gen_search_sql_tuple(smiles, search_type, 2)[1])
    def gen_simi_search_sql(
            self,
            smiles,
            min_simi):
        '''
        gen_simi_search_sql(smiles, min_simi) -- Returns a string.

        args:
            smiles: str, smiles that represents a molecule.
            min_simi: float, the minimal similarity value (tanimoto coefficient)

        tanimoto coefficient
        A is number of ones in fps of mol1
        B is number of ones in fps of mol2
        C is number of ones in A & B
        similarity = C/(A+B-C)

        returns a partial sql string like ' ,tanimoto as similarity FROM ... WHERE ... '
        where 'tanimoto' is the sql string for calculating tanimoto value and 'similarity'
        is the simi_field from env['SIMI_FIELD']
        '''
        s = ''
        s_c = ''
        s_b = ''
        ones_a = 0
        stat = {}
        fps = {}
        min_simi = float(min_simi)
        mol = mymol('smi', smiles)
        mol.get_mol_stat(stat)
        mol.get_fps(fps)
        record_keys = ["NUM_C", "NUM_O", "NUM_N", "NUM_P", "NUM_S", "NUM_F", "NUM_Cl", "NUM_Br", "NUM_I"]
        for i in record_keys:
            if stat.has_key(i) and self.recorded_fields_dict.has_key(i):
                s += self.recorded_fields_dict[i] + " >= " + \
                        str(( lambda x: x == int(x) and int(x) or int(x) + 1 )(min_simi * stat[i])) + \
                        " AND " + self.recorded_fields_dict[i] + " <= " + str(int(1 / min_simi * stat[i])) + ' AND '
        fps_keys = fps.keys()
        fps_keys.remove(self.env['FP_BITS_KEY'])
        fps_keys.sort()
        for i in fps_keys:
            if self.recorded_fields_dict.has_key(i):
                s_b += 'BIT_COUNT(%s) + ' %(self.recorded_fields_dict[i],)
                if fps[i] != 0:
                    s_c += 'BIT_COUNT(%s & %s) + ' %(self.recorded_fields_dict[i], fps[i])
                    #ones_a += str(bin(fps[i])).count('1')
        s_b = ( lambda x: x and '( ' + x + ' )' or '' )( s_b.rstrip('+ ') )
        s_c = ( lambda x: x and '( ' + x + ' )' or '' )( s_c.rstrip('+ ') )
        ones_a = fps[self.env['FP_BITS_KEY']]

        tanimoto = '%s / ( %s + %s - %s )' %(s_c, str(ones_a), s_b, s_c)
        join_part_sql = self.gen_join_part_sql(self.dbd.tables, self.env['PRI_FIELD'])
        return ', %s as %s FROM %s WHERE ( (%s) AND (%s > %s) )' %(
                tanimoto,
                self.env['SIMI_FIELD'],
                join_part_sql,
                s.rstrip(' AND '),
                tanimoto,
                str(min_simi) )

    def gen_adv_search_sql(
        self,
        query,
        smiles_dic = {},
        abbr_dic = {},
        black_words = ['select', 'insert',
            'update', 'drop', 'source']):

        '''
        gen_adv_search_sql(query[, smiles_dic[, abbr_dic[, black_words]]]) -- Returns a string.

        args:
            query: str, the query string.
            smiles_dic: dict, contains the molecules which may be used in the query.
            abbr_dic: dict, the dict of the abbreviated key words.
            black_words: list, the list of the dangerous words.

        returns a partial sql string like ' FROM ... WHERE ... '
        '''
        stats = []
        s = ''
        sub_mols = []
        sup_mols = []
        def gen_re_string(string):
            s = ''
            for i in str(string):
                s += '[' + i + i.upper() + ']'
            return s
        # check if query contains black words
        for i in black_words:
            if re.findall(gen_re_string(i), query):
                raise Exception, 'contains illegal words!'

        # upper case the sql keywords 'and', 'or'
        query = re.sub(r'([aA][nN][dD])|([oO][rR])', lambda g: g.group(0).upper(), query) + ' '
        # add space before and after >, <, =, >=, etc.
        query = re.sub(r' *[><!=]+ *', lambda g: ' ' + g.group(0) + ' ', query)
        # unabbreviating
        r0 = re.compile(r'\w+')
        def repl0(g):
            if abbr_dic.has_key(g.group(0)):
                return abbr_dic[g.group(0)]
            else:
                return g.group(0)
        query = r0.sub(repl0, query)
        # RE for extracting the sub (substructure) part
        re_sub = re.compile(r'[sS][uU][bB] *[!=]+ *[^ )(]*(?=[ )(]+)')
        def repl_sub(g, gen_sql = self.gen_search_sql_tuple):
            sep = ''
            sql = ''
            smi = ''
            g = g.group(0)
            g = g.replace(' ','')
            if re.findall(r'!=', g):
                sep = '!='
                type = '3'
            elif re.findall(r'=', g):
                sep = '='
                type = '2'
            mol_key = g.split(sep)[-1].strip(' ')
            if sep and smiles_dic.has_key(mol_key):
                smi = smiles_dic[mol_key]
                sql = gen_sql(str(smi), str(type), 1)
                stats.append(sql[0])
                return sql[1]
        # RE for extracting the sup (superstructure) part
        re_sup = re.compile(r'[sS][uU][pP] *[!=]+ *[^ )(]*(?=[ )(]+)')
        def repl_sup(g, gen_sql = self.gen_search_sql_tuple):
            sep = ''
            sql = ''
            smi = ''
            g = g.group(0)
            g = g.replace(' ','')
            if re.findall(r'!=', g):
                sep = '!='
                type = '5'
            elif re.findall(r'=', g):
                sep = '='
                type = '4'
            mol_key = g.split(sep)[-1].strip(' ')
            if sep and smiles_dic.has_key(mol_key):
                smi = smiles_dic[mol_key]
                sql = gen_sql(str(smi), str(type), 1)
                stats.append(sql[0])
                return sql[1]

        # get the sub_mols
        for m in re_sub.findall(query):
            if re.findall(r'[^!]=', m):
                mol_key = m.split('=')[-1].strip(' ')
                if smiles_dic.has_key(mol_key) and smiles_dic.get(mol_key):
                    sub_mols.append(smiles_dic.get(mol_key))
        # get the sup_mols
        for m in re_sup.findall(query):
            if re.findall(r'[^!]=', m):
                mol_key = m.split('=')[-1].strip(' ')
                if smiles_dic.has_key(mol_key) and smiles_dic.get(mol_key):
                    sup_mols.append(smiles_dic.get(mol_key))
        # if the query has both sub_mols and sup_mols, then, the sub_mols must be
        # the substructure of sup_mols
        if sup_mols:
            for m in sub_mols:
                mymol_obj = mymol('smi', m)
                for m0 in sup_mols:
                    if not mymol_obj.sub_match('smi', m0):
                        raise Exception, 'sub and sup not match'

        result = re_sub.sub(repl_sub, query)
        result = re_sup.sub(repl_sup, result)

        tmp_dic_sub = {}
        tmp_dic_sup = {}
        stats = [ j for j in stats if j ]
        if stats:
            for i in stats:
                if 'sub' in i.keys():
                    if not tmp_dic_sub:
                        tmp_dic_sub = i['sub']
                        continue
                    else:
                        for k, v in i['sub'].items():
                            if tmp_dic_sub.has_key(k):
                                if tmp_dic_sub[k] < v:
                                    tmp_dic_sub[k] = v
                            else:
                                tmp_dic_sub[k] = v
                elif 'sup' in i.keys():
                    if not tmp_dic_sup:
                        tmp_dic_sup = i['sup']
                        continue
                    else:
                        for k, v in i['sup'].items():
                            if tmp_dic_sup.has_key(k):
                                if tmp_dic_sup[k] < v:
                                    tmp_dic_sup[k] = v
                            else:
                                tmp_dic_sup[k] = v

            val_k = ''
            for k, v in tmp_dic_sub.items():
                for j in self.def_dict.values():
                    if j.has_key(k):
                        val_k = j[k][0]
                        break
                if val_k:
                    if tmp_dic_sup.has_key(k):
                        if int(v) == int(tmp_dic_sup[k]):
                            s += '%s = %s AND ' %(str(val_k), str(v))
                        elif int(v) > int(tmp_dic_sup[k]):
                            raise Exception, 'mol stat range err'
                        else:
                            s += '%s >= %s AND %s <= %s AND ' %(str(val_k), str(v), str(val_k), str(tmp_dic_sup[k]))
                    else:
                        s += str(val_k) + ' >= ' + str(v) + ' AND '

            for k, v in tmp_dic_sup.items():
                if k in tmp_dic_sub.keys():
                    continue
                else:
                    for j in self.def_dict.values():
                        if j.has_key(k):
                            val_k = j[k][0]
                            break
                    if val_k:
                        s += str(val_k) + ' <= ' + str(v) + ' AND '

            result = '(%s) AND (%s)' %(s.rstrip(' AND '), result.strip(' '))

        join_part_sql = self.gen_join_part_sql(self.dbd.tables, self.env['PRI_FIELD'])
        return ' FROM %s WHERE (%s)' %(join_part_sql, result)

    def gen_sql_head(self, def_file = None):
        '''
        gen_sql_head() -- Returns a dict.

        returns a dict contains the 'creat' sentences of each table according to the sdf-to-sql define file
        '''
        result = {}
        pri_field = ''
        if def_file:
            dbd = dbdef(def_file)
        else:
            dbd = self.dbd

        for k, v in dbd.ordered_fields_dict.items():
            if not k in result.keys():
                result[k] = 'CREATE TABLE IF NOT EXISTS `%s` (\n' %k
            for k0 in v:
                comment_str = '%s'
                default_str = '%s'
                key_defs = dbd.key_defs_dict(k0.keys()[0])
                if key_defs['COMMENT']:
                    comment_str = " COMMENT '%s'"
                if key_defs['DEFAULT_VALUE']:
                    default_str = " DEFAULT '%s'"
                string = "\t`%s` %s" + default_str + comment_str + ",\n"
                result[k] += string %(
                        key_defs['MYSQL_FIELD'],
                        key_defs['MYSQL_FIELD_TYPE'],
                        key_defs['DEFAULT_VALUE'],
                        key_defs['COMMENT'] )
                if key_defs['PIC'].startswith('INDEX'):
                        ind_len = key_defs['PIC'].split(',')[1]
                        if ind_len:
                            result[k] += "\tINDEX (%s(%s)),\n" %(key_defs['MYSQL_FIELD'], ind_len)
                        else:
                            result[k] += "\tINDEX (%s),\n" %key_defs['MYSQL_FIELD']
                elif key_defs['PIC'].startswith('PRIMARY'):
                    pri_field = key_defs['MYSQL_FIELD']
            result[k] += '\tPRIMARY KEY (`%s`)\n' %pri_field + ') %s;\n' %dbd.table_args[k]
        return result

    def gen_insert_sqls(self, values_dict, action = 'INSERT', show_head = True):
        '''
        gen_insert_sql(values_dict[, actions]) -- Returns a list.

        args:
            values_dict: dict, contains the keys and values, in which the keys are only those can
                be found in the sdf-to-sql define file.
            action: string, can be 'REPLACE' and 'INSERT'.
            show_head: bool, show the 'INSERT INTO ...' part or not

        returns the sqls(partial, without the where part) in a list from the given values_dict
        according to the definations of sdf-to-sql file
        '''
        fields = {}
        values = {}
        l = []
        val = ''
        repl = lambda x: '\\' + x.group(0)
        if action not in ('REPLACE', 'INSERT'):
            action = 'REPLACE'
        all_keys = self.dbd.recorded_fields_dict().keys()
        all_keys.sort()
        for k in all_keys:
            if k in values_dict.keys():
                v = values_dict[k]
            else:
                v = ''
            try:
                v = re.sub(r'''['"&%\\]''', repl, v)
            except:
                pass
            key_defs = self.dbd.key_defs_dict(k)
            if key_defs:
                table = key_defs['TABLE']
                if not values.has_key(table):
                    if show_head:
                        values[table] = '%s INTO %s(%s) VALUES (' %(action, table, '%s')
                    else:
                        values[table] = '('
                if not fields.has_key(table):
                    fields[table] = []
                if key_defs['PIC']:
                    # compress the 'COMPRESS' flaged thing
                    if key_defs['PIC'].startswith('COMPRESS'):
                        val = '0x' + zlib.compress(v).encode('hex') + ", "
                    else:
                        val = "'" + str(v) + "', "
                else:
                    val = "'" + str(v) + "', "
                fields[table].append(key_defs['MYSQL_FIELD'])
                if str(v):
                    values[table] += val
                else:
                    values[table] += "'%s', " %key_defs['DEFAULT_VALUE']

        tables = fields.keys()
        tables.sort()
        results = {}
        for k in tables:
            if show_head:
                results[k] = (values[k] %', '.join(fields[k])).rstrip(', ') + ')'
            else:
                results[k] = values[k].rstrip(', ') + ')'
        return results
