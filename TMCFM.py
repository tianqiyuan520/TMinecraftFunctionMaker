import math
import json
import os
from read_config import read_json
D_PATH = ''
D_NAME = ''
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
        cfg = read_json.read('config.json')
        #清除文件
        if (cfg["is_rewrite"]):
            os.remove(cfg["path"])

        PATH = cfg['path'] # 项目地址
        global D_NAME
        D_NAME = cfg['path'] # 项目名称
        folder = os.path.exists(PATH)
        if not folder:
            os.makedirs(PATH)
        folder = os.path.exists(PATH+'data')
        if not folder:
            os.makedirs(PATH+'data')
        description = cfg['description'] if isinstance(cfg['description'],list) else "\"" + str(cfg['description']) + "\""
        f = open(PATH + 'pack.mcmeta','w',encoding='utf-8')
        f.write(
f'''{{
  "pack": {{
    "pack_format": {cfg['pack_format']},
    "description": {description}
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
        print(D_PATH)

        
    def main(self):
        self.parse(self.content)

    def parse(self,value:list) -> list:
        '''解析'''
        Parser(value)
