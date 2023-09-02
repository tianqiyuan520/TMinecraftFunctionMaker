import math
import json
import os
import shutil
from read_config import read_json
D_PATH = ''
D_NAME = ''
Pathtime = 0
from Parser import Parser

class TMCFM:
    def __init__(self,content,time):
        # print('init...')
        self.content = content
        global Pathtime
        Pathtime = time
        self.init_datapack()
        # print('content: \n',content)
        # print('init success')
    def init_datapack(self):
        '''初始化数据包文件'''
        global Pathtime
        try:
            cfg = read_json.read('config.json')['config']
            #重置 整个数据包
            if (cfg["is_rebuild"]) and os.path.exists(cfg['path'][Pathtime]):
                # os.remove()
                shutil.rmtree(cfg['path'][Pathtime])

            PATH = cfg['path'][Pathtime] # 项目地址
            global D_NAME
            D_NAME = cfg['path'][Pathtime] # 项目名称
            if not os.path.exists(PATH):
                try:
                    os.makedirs(PATH)
                except:
                    try:
                        os.makedirs(PATH)
                    except:
                        ...
            if not os.path.exists(PATH+'data'):
                try:
                    os.makedirs(PATH+'data')
                except:
                    try:
                        os.makedirs(PATH+'data')
                    except:
                        ...
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
            PATH = cfg['path'][Pathtime]+'data\\' # 项目地址
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
        finally:
            ...

        
    def main(self):
        self.parse(self.content)

    def parse(self,value:list) -> list:
        '''解析'''
        Parser(value)
