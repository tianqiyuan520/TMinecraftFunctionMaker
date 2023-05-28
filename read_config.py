import json

class read_json:
    def __init__(self,path):
        ...
    def read(path) -> json: 
        with open(path,"r",encoding='utf-8') as f:
            file = json.load(f)
        return file

class System_i_functions:
    def __init__(self) -> None:
        ...
    def read() -> json:
        with open('system//system_function.json',"r",encoding='utf-8') as f:
            file = json.load(f)
        return file
