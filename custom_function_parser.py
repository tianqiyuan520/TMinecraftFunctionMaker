import json
import os
import re

from read_config import System_i_functions
class Custom_Fuc_Parser(System_i_functions):
    def __init__(self) -> None:
        ...
    def read() -> json:
        custom_functions = []
        for filepath,dirnames,filenames in os.walk(r'system'):
            for filename in filenames:
                if '.json' in filename and filename != "system_function.json":
                    with open(r'{}'.format(os.path.join(filepath,filename)),'r',encoding='utf-8') as f:
                        text = json.load(f)
                    custom_functions.append(text)
        return custom_functions
    def build_py():
        for filepath,dirnames,filenames in os.walk(r'system'):
            for filename in filenames:
                if '.json' in filename and filename != "system_function.json":
                    with open(r'{}'.format(os.path.join(filepath,filename)),'r',encoding='utf-8') as f:
                        text = json.load(f)
                    with open(r'{}'.format(os.path.join(filepath,str(text["name"])+'.py')),'w',encoding='utf-8') as f:
                        for i in text['functions']:
                            args = ""
                            for j in range(len(i['args'])):
                                args += f",input{j}"
                            args = args[1:]
                            python_code = ''
                            if i.get('python_code'):
                                python_code = i['python_code']
                            code = ""
                            for j in python_code:
                                code +="    "+j+"\n"
                            f.write(f"def {i['name']}({args}):\n    \"\"\"{str(i['description'])}\"\"\"\n{code}")

Custom_Fuc_Parser.build_py()