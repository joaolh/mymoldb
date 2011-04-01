#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Name:     chem2pic.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Licence:  GPLv3
# Version:  110401

from indigo import *
from indigo_renderer import *
import os, sys, pybel
from hashlib import md5

class mol2pic():
    def __init__(self, string, out_file, out_fmt = 'png', width = 600, height = 600):
        self.out_file = out_file
        self.idg = Indigo()
        self.renderer = IndigoRenderer(self.idg)
        self.idg.setOption("render-output-format", out_fmt)
        self.idg.setOption("render-comment-position", "top")
        self.idg.setOption("render-image-size", width, height)
        self.idg.setOption("render-background-color", 1.0, 1.0, 1.0)
        self.idg.setOption('render-label-mode', 'forcehide')
        self.idg.setOption('render-margins', 5, 5)
        self.idg.setOption('render-coloring', True)
        self.idg.setOption('render-stereo-old-style', True)
        if os.path.exists(string):
            self.mol = self.idg.loadMoleculeFromFile(string)
        else:
            self.mol = self.idg.loadMolecule(string)
    def gen_pic(self, auto_layout = True):
        if auto_layout:
            self.mol.layout()
        self.renderer.renderToFile(self.mol, self.out_file)
        return True

class mol():
    def __init__(self, fmt, string, auto_layout = False):
        self.mol_pic_path = ''
        self.auto_layout = auto_layout
        self.fmt = fmt
        self.string = string
        if self.fmt in ('smi', 'smiles', 'sma', 'smarts', 'inchi'):
            self.auto_layout = True
        if self.auto_layout:
            self.flag = 'auto-'
        else:
            self.flag = 'orig-'
        self.mol = None
        if not self.fmt in ('mol', 'sdf', 'sd', 'cml', 'smi', 'smiles', 'sma', 'smarts'):
            self.mol = pybel.readstring(self.fmt, self.string)
            self.string = self.fmt_conv('mol')
            self.fmt = "mol"
        if self.fmt in ('smi', 'smile', 'sma', 'smarts'):
            self.string = '.'.join([i.split('\t')[0] for i in self.string.split('\n')])

    def gen_mol_pic(self, mol_pic_dir = "./", mol_pic_path = None):
        self.mol_pic_path = mol_pic_path
        if not mol_pic_path:
            self.mol_pic_path = mol_pic_dir.rstrip(os.sep) + os.sep + self.flag + md5(self.string).hexdigest() + '.png'
        if os.path.exists(self.mol_pic_path):
            print 'Warning: path exists!'
        else:
            mol2pic(self.string, self.mol_pic_path).gen_pic(self.auto_layout)

    def fmt_conv(self, out_fmt):
        try:
            return self.mol.write(out_fmt)
        except:
            return ''

if __name__ == '__main__':
    viewcmd = 'xdg-open'
    mol_pic_dir = './'
    if not os.path.exists(mol_pic_dir):
        os.mkdir(mol_pic_dir)

    if len(sys.argv) == 1:
        print "%s /path/to/chemfiles" %sys.argv[0]
    elif len(sys.argv) >= 3:
        if sys.argv[1] == '-a':
            m = mol(sys.argv[2], sys.argv[3], True)
        else:
            m = mol(sys.argv[2], sys.argv[3], False)

        try:
            m.gen_mol_pic()
            mol_pic_path = m.mol_pic_path
        except Exception, e:
            print e
            mol_pic_path = mol_pic_dir.rstrip(os.sep) + os.sep + 'failed.png'
    print mol_pic_path
    os.system("%s %s" %(viewcmd, mol_pic_path))
