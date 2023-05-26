##TMCFM编译器
##将类似python的语言转化为Minecraft数据包
'''
author:天起源
'''
import math
from TMCFM import TMCFM
import re
import ast,astunparse,json


if __name__ == "__main__":
    #open file
    content = ""
    with open('a.py','r',encoding='utf-8') as f:
        # content = f.read().split('\n')
        content = f.read()
    # content = input('>>> ')
    comp = TMCFM(content)
    # print(content)
    comp.main()
    input()