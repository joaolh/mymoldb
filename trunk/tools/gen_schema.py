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
    db = raw_input('Choose db in ' + ', '.join(ENVS.keys()) + ': ')
    f = open(sys.argv[1], 'w')
    sql_obj = sql(ENVS[db])
    for v in sql_obj.gen_sql_head().values():
        f.write(v + '\n')
    f.close()
