#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     mol.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  100305

import sys, pybel, zlib, os, re, openbabel as ob
from functions import md5

class sdf():
    @classmethod
    def sdf_to_list(self, sdf_file):
        '''
        sdf_to_list(sdf_file) -- Returns a list contains the mol info.

        parse mol info in a sdf file to a list (one mol per element in list).
        '''
        l = ""
        line = ""
        sdfs = []
        for line in open(sdf_file):
            if (line.startswith("$$$$")) and l:
                sdfs.append(l)
                l = ""
            else:
                # some times the first line of the sdf may be $$$$, skip such lines
                if not line.startswith("$$$$"):
                    l += line
        if l.replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '') != '':
            sdfs.append(l)
            l = ""
        return sdfs

    @classmethod
    def mol_parse(self, sdf_string, compress_list = []):
        '''
        mol_parse(sdf_string[, compress_list]) -- Returns a dict contains the mol info.

        args:
            sdf_string: str, sdf text
            compress_list: list, keys of the dict whose value you want to compress

        parse fileds from the sdf text. one molecular once.
        '''
        l = []
        L = []
        l = sdf_string.split("> <")
        L = [i.strip().split(">\n") for i in l]
        L[0].insert(0, "MOL_2D_STRUC")
        try:
            dic = dict(L)
        except:
            L.pop()
            dic = dict(L)
        if compress_list:
            for k, v in dic.items():
                if k in compress_list and v:
                    dic[k] = '0x' + zlib.compress(v).encode('hex')
        return dic

class mymol():
    def __init__(
            self,
            format,
            string,
            recorded_elements = ["C", 'H', "O", "N", "P", "S", "F", "Cl", "Br", "I"]):
        '''
        args:
            format: str, could be 'smi', 'mol' and 'xyz' etc., see openbabel formats.
            string: str, the content of a molecule in the format of format.
            recorded_elements: list, the elements to record.
        '''
        self.mol = pybel.readstring(str(format), str(string))
        self.format = format
        # make a temp mol for the similarity calculating
        query_mol = pybel.readstring('smi', 'C')
        self.query_mol_fps = query_mol.calcfp()
        self.fps = self.mol.calcfp()
        self.mol_string = string
        self.recorded_elements = recorded_elements
    def get_mol_data(self, data = {}):
        '''
        get_mol_data([data]) -- Returns a dict.
        calculats the mol data

        args:
            data: dict, in which the data stores.
        '''
        desc = self.mol.calcdesc()
        ob_can_smi = self.gen_openbabel_can_smiles()
        data.update( {
                'TPSA': desc['TPSA'],
                'LogP': desc['logP'],
                'MR': desc['MR'],
                'FORMULA': self.mol.formula,
                'MOLWEIGHT': self.mol.molwt,
                'EXACTMASS': self.mol.exactmass,
                'CHARGE': self.mol.charge,
                'OPENBABEL_CAN_SMILES': ob_can_smi,
                'MD5_OPENBABEL_CAN_SMILES': md5(ob_can_smi)
                } )
        return data

    @classmethod
    def mol_data_keys(self):
        '''
        mol_data_keys() -- Returns a list.
        returns the keys of the mol_data part
        '''
        return ['TPSA', 'LogP', 'MR', 'FORMULA', 'MOLWEIGHT', 'EXACTMASS', 'CHARGE',
                'OPENBABEL_CAN_SMILES', 'MD5_OPENBABEL_CAN_SMILES']

    def gen_openbabel_can_smiles(self):
        '''
        gen_openbabel_can_smiles() -- Returns a smiles string.
        generates the openbabel canonical smiles.
        '''
        return self.mol.write("can").strip('\t\n').split("\t")[0]

    def removeh(self, out_format = 'mol'):
        '''
        removeh([out_format]) -- Returns a mol string with out element H presented.

        args:
            out_format: str, the output format of the molecule, could be mol, xyz, etc.
                default is mol

        removes the element H in the mol file, so the picture you draw with this
        mol file might be nicer.
        '''
        self.mol.removeh()
        return self.mol.write(str(out_format))

    def sub_match(self, format, string):
        '''
        sub_match(format, string) -- Returns a list.

        args:
            format: str, str, could be 'smi', 'mol' and 'xyz' etc., see openbabel formats.
            string: str, the content of a molecule in the format of format.

        returns all matches of the smarts pattern to a particular molecule
        presented by a given smiles string. If the result is not null, then self.mol is a
        substructure of molecule presented by string.
        '''
        smarts = self.gen_openbabel_can_smiles()
        try:
            return pybel.Smarts(smarts).findall(pybel.readstring(str(format), str(string)))
        except:
            return False

    def sup_match(self, format, string):
        '''
        sup_match(format, string) -- Returns a list.

        args:
            format: str, str, could be 'smi', 'mol' and 'xyz' etc., see openbabel formats.
            string: str, the content of a molecule in the format of format.

        returns all matches of a particular molecule presented by a given smiles string to self.mol
        if the result is not null, then self.mol is a superstructure of molecule presented by string.
        '''
        smarts = pybel.readstring(str(format), str(string)).write("can").strip('\t\n')
        try:
            return pybel.Smarts(smarts).findall(self.mol)
        except:
            return False

    def get_fps(self, fps = {}):
        '''
        get_fps([fps]) -- Returns a dict.

        args:
            fps: dict, stores the results inside.

        generates fingerprint of the molecule.
        '''
        j = 1
        l = []
        FP = self.mol.calcfp()
        fps["FP_BITS"] = len(FP.bits)
        for fp in FP.fp:
            l.append(fp)
        for i in range(len(l)):
            fps["FP" + "%.2d" %(j,)] = l[i]
            j += 1
        return fps
    @classmethod
    def fps_keys(self):
        '''
        fps_keys() -- Returns a list.

        return the keys of the fingerprint part
        '''
        l = []
        l.append('FP_BITS')
        for i in range(1, 33):
            l.append("FP" + "%.2d" %(i,))
        return l

    def get_mol_stat(
            self,
            stat = {},
            recorded_elements = ["C", 'H', "O", "N", "P", "S", "F", "Cl", "Br", "I"]
            ):
        '''
        get_mol_stat([stat[, recorded_elements]]) -- Returns a dict.

        args:
            stat: dict, stores the results inside.
            recorded_elements, list, contains elements whose number in a molecule you want to record.

        get the molecular statistics.
        '''
        # ring number and ring size
        mol = self.mol
        # number of rings
        stat["NUM_RINGS"] = len(mol.sssr)
        # add H to the molecular to calc the total atom number
        mol.addh()
        stat["NUM_ATOMS"] = len(mol.atoms)

        # get number of elements and number of different element types
        l = []
        num_other = 0
        for m in mol.atoms:
            atom_name = m.type[0]
            atom_type = m.type
            # atom_name and atom_type maybe equal, so use set to deduplicate
            l = list(set([atom_name, atom_type]))
            for i in l:
                if i[0] in self.recorded_elements:
                    key = "NUM_" + i
                    if stat.has_key(key):
                        stat[key] += 1
                    else:
                        stat[key] = 1
                else:
                    num_other += 1
        stat["NUM_X"] = num_other

        # number of bonds (using openbabel because of the lack of such thing in pybel)
        mol_ob = ob.OBMol()
        obc = ob.OBConversion()
        obc.SetInFormat(self.format)
        obc.ReadString(mol_ob, self.mol_string)
        mol_ob.AddHydrogens()
        if mol_ob.NumBonds() > 0:
            stat["NUM_BONDS"] = mol_ob.NumBonds()

        # get rings
        rings = []
        for r in mol.sssr:
            rings.append(r.Size())
        for r in rings:
            if r > 8:
                key = "NUM_RX"
            else:
                key = "NUM_R" + str(r)
            if stat.has_key(key):
                stat[key] += 1
            else:
                stat[key] = 1
        return stat
    @classmethod
    def mol_stat_keys(self, recorded_elements = ["C", 'H', "O", "N", "P", "S", "F", "Cl", "Br", "I"]):
        '''
        mol_stat_keys() -- Returns a list.

        return the keys of the mol_stat part
        '''
        l = ['NUM_RINGS', 'NUM_ATOMS', 'NUM_BONDS', 'NUM_X', 'NUM_RX',
            'NUM_C1', 'NUM_C2', 'NUM_C3', 'NUM_O2', 'NUM_O3', 'NUM_N1',
            'NUM_N2', 'NUM_N3', 'NUM_S2', 'NUM_S3', 'NUM_Car', 'NUM_Nar']
        l += [ 'NUM_R' + str(i) for i in range(3, 9) ] + [ 'NUM_' + i for i in recorded_elements ]
        return l
    def simi_calc(self, format, foo):
        '''
        simi_calc(format, string) -- Return the tanimoto similarity value.

        args:
            format: str, str, could be 'smi', 'mol' and 'xyz' etc., see openbabel formats.
                a fps list is also available here given the format 'fps'
            string: str, the content of a molecule in the format of format.

        this function calculats the taninoto similarity between the given molecule and mymol
        '''
        if format == 'fps':
            # make a temp mol object
            query_mol_fps = self.query_mol_fps
            # add the precalculated fps to the temp mol, thus we can calculat the similarity between
            # the query mol (whose fingerprint had been precalculated) and self.mol
            query_mol_fps.fp = foo
        else:
            query_mol_fps = pybel.readstring(format, foo).calcfp()
        return self.fps | query_mol_fps

    @classmethod
    def all_keys(self):
        '''
        all_keys() -- Returns a list.

        returns all the keys of the properties which can be calculated in this class.
        '''
        return self.mol_data_keys() + self.fps_keys() + self.mol_stat_keys()
