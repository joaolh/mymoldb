#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     genpic.py
# Author:   xiooli <xioooli[at]yahoo.com.cn>
# Site:     http://joolix.com
# Licence:  GPLv3
# Version:  091218

'''用于产生网站验证码图片(代数算式)'''

import Image,ImageDraw,ImageFont
import random
import math
import hashlib
import datetime
import os
from settings import http_path, verpic_path

def genpic():
    '''生成验证码图片,返回一个元组(filename,result)'''
    #图片宽度
    width = 130
    #图片高度
    height = 35
    #背景颜色
    bgcolor = (151, random.randint(0,225), random.randint(0,225))
    #生成背景图片
    image = Image.new('RGB',(width,height),bgcolor)
    #加载字体
    font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',27)
    #字体颜色
    fontcolor = (0, 0, 0)

    #产生draw对象
    draw = ImageDraw.Draw(image)

    # 生成算式
    ops = ['+', '-']
    op = random.choice(ops)
    num1 = random.randint(0, 99)
    num2 = random.randint(0, 99)
    rand_str = str(num1) + op + str(num2)
    result = str(eval(rand_str))

    # 生成文件名
    m = hashlib.md5()
    m.update(str(datetime.datetime.now()))
    fnm = m.hexdigest() + '.jpg'

    #画字体,(0,0)是起始位置
    draw.text((0,0),rand_str + ' =',font=font,fill=fontcolor)

    #画线
    #线的颜色
    linecolor= (random.randint(0,225), random.randint(0,225), random.randint(0,225))
    for i in range(0,15):
        #随机产生线条
        x1 = random.randint(0,width)
        x2 = random.randint(0,width)
        y1 = random.randint(0,height)
        y2 = random.randint(0,height)
        draw.line([(x1, y1), (x2, y2)], linecolor)

    #释放draw
    del draw

    #保存文件到本地
    image.save(http_path + verpic_path + fnm)
    return (verpic_path + fnm, result)

def delpic(picfile):
    '''delete the given pic file'''
    picpath = http_path + picfile
    try:
        os.system("rm " + picpath)
    except:
        pass

if __name__ == "__main__":
    pic = genpic()
    print pic
