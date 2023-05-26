##TMCFM编译器
##将类似python的语言转化为Minecraft数据包
'''
author:天起源
'''
import ast
from TMCFM import TMCFM


if __name__ == "__main__":
    #open file
    content = ""
    with open('a.py','r',encoding='utf-8') as f:
        # content = f.read().split('\n')
        content = f.read()
    # content = input('>>> ')
    code_ = ast.parse(content)
    print(ast.dump(code_))
    # comp = TMCFM(content)
    # print(content)
    # comp.main()