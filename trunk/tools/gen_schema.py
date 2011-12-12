#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     gen_schema.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  100908

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))
from libmymoldb import sql
from settings import ENVS

if len(sys.argv) < 2:
    print 'Useage: ' + sys.argv[0] + ' output.sql'
    sys.exit(1)
else:
    dbs = []
    for k, v in ENVS.items():
        if v.has_key('DEF_FILE'):
            dbs.append(k)
    db = None
    while not db in dbs:
        db = raw_input('Please choose db in ( %s ): ' %', '.join(dbs))
        if not db in dbs:
            print 'Error, db name not valid!'
    try:
        f = open(sys.argv[1], 'w')
        sql_obj = sql(ENVS[db])
        for v in sql_obj.gen_sql_head().values():
            f.write(v + '\n')
        f.close()
        print '%s successfully generated! Now you can execute the generated sql file to create a new database.' %sys.argv[1]
    except Exception, e:
        print e
