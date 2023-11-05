import json
import os

from config import custom_functions  # 自定义 函数调用表
from config import defualt_DataPath  # 项目Data文件路径
from config import defualt_NAME  # 项目名称
from config import defualt_PATH  # 默认路径
from config import defualt_STORAGE  # STORAGE
from config import scoreboard_objective  # 默认记分板
from config import system_functions  # 内置 函数调用表

#更新配置
def update_config_call(function):
    def wrapper(*args,**kwargs):
        update_config()
        return function(*args,**kwargs)
    return wrapper

def update_config():
    from TMCFM import Pathtime
    cfg = read_json.read('config.json')['config']
    global defualt_DataPath
    global defualt_PATH
    defualt_DataPath = cfg['path'][Pathtime]+"data/"
    defualt_PATH = cfg['path'][Pathtime]+"data/"+cfg['name'] + '/'

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



class editor_file:
    def __init__(self):
        ...
    @update_config_call
    def write_file(self,func:str,text:str,*args,**kwargs):
        '''读写函数 f2为函数详细名称,p为函数的相对位置'''
        
        try:
            if self.stack_frame[-1]['Is_code_have_end'] == False and self.stack_frame[-1]["In_loop"] == False:
                text = text.replace(f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ","")
                
            # elif text[0] != "#":
                # text = f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ' + text
        except:
            ...
        func2 = '_start'
        PATH_ = None
        mode = "a"
        ClassName = ""
        Is_def_func = False
        inNewFile = False
        for key, value in kwargs.items():
            if((key=='f2'or key ==  'func2') and value != None):
                func2 = value
            elif(key=='p'or key ==  'path'):
                PATH_ = value
            elif((key=='c'or key ==  'ClassName' )and value != None):
                ClassName = value
            elif(key=='Is_new_function' and value == True):
                Is_def_func = True
            elif(key=='inNewFile' and value == True):
                inNewFile = True
            elif(key=='FunctionPath'):
                ## 函数的相对路径
                Is_def_func = True
            elif(key=='mode'):
                ## 读写模式
                mode = value
        if(Is_def_func) and not inNewFile:
            PATH_ = None
        if ClassName != "":
            ClassName = ClassName+'/'
        if(PATH_==None):
            path = defualt_PATH+'functions/'+ClassName+func+'/'
            func_path = defualt_PATH+'functions/'+ClassName+func+'/'+func2+'.mcfunction'
            folder = os.path.exists(path)
            if not folder:
                os.makedirs(path)
            folder = os.path.exists(func_path)
            if folder:
                with open(func_path,mode,encoding='utf-8') as f:
                    f.write(text)
            else:
                with open(func_path,"w",encoding='utf-8') as f:
                    f.write(text)
        else:
            PATH_ = defualt_PATH+'functions/'+ClassName+PATH_
            if(PATH_[-1]!="/"):
                PATH_ += "/"
            func_path = PATH_+func2+'.mcfunction'
            folder = os.path.exists(PATH_)
            if not folder:
                os.makedirs(PATH_)
            folder = os.path.exists(func_path)
            if folder:
                with open(func_path,mode,encoding='utf-8') as f:
                    f.write(text)
            else:
                with open(func_path,'w',encoding='utf-8') as f:
                    f.write(text)
        return self
    @update_config_call
    def WriteT(self,text,name="1",path=defualt_PATH,*args,**kwargs):
        '''读写文件'''
        mode = "a"
        for key, value in kwargs.items():
            if(key=='mode'):
                ## 读写模式
                mode = value
        
        folder = os.path.exists(path)
        if not folder:
            os.makedirs(path)
        file_path = path if path[-1] == '/' else path + '/'
        folder = os.path.exists(file_path)
        if folder:
            with open(file_path+name,mode,encoding='utf-8') as f:
                f.write(text)
        else:
            with open(file_path+name,"w",encoding='utf-8') as f:
                f.write(text)

    # 删除文本
    def remove_text(self,func:str,text:str,newText:str,time:int,*args,**kwargs):
        '''读写函数 f2为函数详细名称,p为函数的相对位置'''
        func2 = '_start'
        PATH_ = None
        mode = "a"
        ClassName = ""
        Is_def_func = False
        for key, value in kwargs.items():
            if((key=='f2'or key ==  'func2') and value != None):
                func2 = value
            if(key=='p'or key ==  'path'):
                PATH_ = value
            if((key=='c'or key ==  'ClassName' )and value != None):
                ClassName = value
            if(key=='Is_new_function' and value == True):
                Is_def_func = True
            if(key=='FunctionPath'):
                ## 函数的相对路径
                Is_def_func = True
            if(key=='mode'):
                ## 读写模式
                mode = value
        if(Is_def_func):
            PATH_ = None
        if ClassName != "":
            ClassName = ClassName+'/'
        if(PATH_==None):
            path = defualt_PATH+'functions/'+ClassName+func+'/'
            func_path = defualt_PATH+'functions/'+ClassName+func+'/'+func2+'.mcfunction'
            folder = os.path.exists(path)
            if not folder:
                os.makedirs(path)
            folder = os.path.exists(func_path)
            new_text = []
            if folder:
                with open(func_path,"r",encoding='utf-8') as f:
                    new_text = f.readlines()
                with open(func_path,"w",encoding='utf-8') as f:
                    for i in new_text:
                        if time and i.find(text) != -1:
                            i = i.replace(text,newText)
                            time -= 1
                        f.write(i)
        else:
            PATH_ = defualt_PATH+'functions/'+ClassName+PATH_
            if(PATH_[-1]!="/"):
                PATH_ += "/"
            func_path = PATH_+func2+'.mcfunction'
            folder = os.path.exists(PATH_)
            if not folder:
                os.makedirs(PATH_)
            folder = os.path.exists(func_path)
            new_text = []
            if folder:
                with open(func_path,"r",encoding='utf-8') as f:
                    new_text = f.readlines()
                with open(func_path,"w",encoding='utf-8') as f:
                    for i in new_text:
                        if time and i.find(text) != -1:
                            i = i.replace(text,newText)
                            time -= 1
                        f.write(i)
        return self