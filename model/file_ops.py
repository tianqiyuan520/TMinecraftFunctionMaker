import json
import os
class file_ops:
    def __init__(self) -> None:
        pass
class read_json:
    def __init__(self):
        ...
    def read(path) -> json: 
        with open(path,"r",encoding='utf-8') as f:
            try:
                file = json.load(f)
            except:
                print('Json 解析文件失败')
                file = 'Json 解析文件失败'
        return file