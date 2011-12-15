#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     sdfparser.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  100228

'''parse the pubchem sdf file and translate it into sql file according to the def file'''
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))
import openbabel as ob
from libmymoldb import sdf, mymol, sql
from libmymoldb.functions import md5
from settings import ENVS

if __name__ == "__main__":

    savedir = 'sqls'
    if len(sys.argv) < 2:
        print "useage: python " + sys.argv[0] + " input.sdf [database name] [save dir]"
        sys.exit(1)
    elif len(sys.argv) < 3:
        db = raw_input('Choose a database: ' + ', '.join(ENVS.keys()) + ': ')
    elif len(sys.argv) == 4:
        savedir = sys.argv[3]
    else:
        db = sys.argv[2]

    try:
        sdf_file = sys.argv[1]
        if not os.path.exists(sdf_file):
            print "sdf input file not exist"
            sys.exit(1)
        if not os.path.exists(ENVS[db]['DEF_FILE']):
            print "def file not exist"
            sys.exit(1)
    except:
        print "useage: python " + sys.argv[0] + " input.sdf [database name] [save dir]"
        sys.exit(1)

    env = ENVS[db]
    print savedir
    if not os.path.exists(savedir):
        os.mkdir(savedir)

    L = sdf.sdf_to_list(sdf_file)
    tmp_dict = {}
    result = {}
    num_rec = 0
    total_rec = 0
    len_L = len(L)
    s = ''
    add_head = True
    smi_key = 'PUBCHEM_OPENEYE_CAN_SMILES'
    mol_id_key = 'PUBCHEM_COMPOUND_CID'
    results = {}

    for n, i in enumerate(L):
        m = sdf.mol_parse(i)
        try:
            smi = m[smi_key]
        except:
            total_rec += 1
            continue
        mol_id = m[mol_id_key]
        for id_key in env['PRI_KEYS']:
            tmp_dict[id_key] = mol_id
        mol = mymol('smi', smi)
        mol.get_fps(tmp_dict)
        mol.get_mol_stat(tmp_dict)
        mol.get_mol_data(tmp_dict)
        tmp_dict.update(m)

        sql_obj = sql(env)
        num_rec += 1
        total_rec += 1
        for k, v in sql_obj.gen_insert_sqls(tmp_dict, 'INSERT', add_head).items():
            try:
                results[k] += v + '\n'
            except:
                results[k] = v + '\n'
        add_head = add_head and False
        if num_rec == 5000 or total_rec == len_L or n+1 == len(L):
            for k, v in results.items():
                open(savedir + '/' + sdf_file.replace('.sdf', '') + '_' + k + '.sql', 'a').write(v)
            num_rec = 0
            results = {}
            tmp_dict = {}
