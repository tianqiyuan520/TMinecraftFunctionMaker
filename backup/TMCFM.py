import math
import json
import os

D_PATH = ''
from Parser import Parser

class TMCFM:
    def __init__(self,content):
        
        # print('init...')
        self.content = content
        self.init_datapack()
        # print('content: \n',content)
        # print('init success')
    def init_datapack(self):
        '''初始化数据包文件'''
        with open('config.json',"r",encoding='utf-8') as j:
            cfg = json.load(j)['config']
        PATH = cfg['path'] # 项目地址
        folder = os.path.exists(PATH)
        if not folder:
            os.makedirs(PATH)
        folder = os.path.exists(PATH+'data')
        if not folder:
            os.makedirs(PATH+'data')
        f = open(PATH + 'pack.mcmeta','w',encoding='utf-8')
        f.write(
f'''{{
  "pack": {{
    "pack_format": {cfg['pack_format']},
    "description": {cfg['description']}
  }}
}}''')
        f.close()
        PATH = cfg['path']+'data\\' # 项目地址
        folder = os.path.exists(PATH+cfg['name'])
        if not folder:
            os.makedirs(PATH+cfg['name'])
        folder = os.path.exists(PATH+'minecraft')
        if not folder:
            os.makedirs(PATH+'minecraft')
        PATH = PATH+cfg['name'] + '\\'
        for i in ['advancements','functions','predicates','tags']:
            folder = os.path.exists(PATH+i)
            if not folder:
                os.makedirs(PATH+i)
        global D_PATH
        D_PATH =  PATH #全局保存该数据包该命令空间下的路径


        
    def main(self):
        self.parse(self.content)

    def parse(self,value:list) -> list:
        '''解析'''
        Parser(value)
