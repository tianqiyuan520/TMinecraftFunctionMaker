import ast
from model.mcf_modifier import mcf_modifier
from config import custom_functions  # 自定义 函数调用表
from config import defualt_DataPath  # 项目Data文件路径
from config import defualt_NAME  # 项目名称
from config import defualt_PATH  # 默认路径
from config import defualt_STORAGE  # STORAGE
from config import scoreboard_objective  # 默认记分板
from config import system_functions  # 内置 函数调用表
from model.file_ops import editor_file

class py_modifier(mcf_modifier):
    def __init__(self):
        self.stack_frame = []
        # 添加栈 *
    def py_append_tree(self):
        '''新建堆栈值'''
        self.stack_frame.append({"data":[],"is_break":0,"is_continue":0,"return":[],"type":"","is_return":0,"is_end":0,"exp_operation":[],"functions":[],"BoolOpTime":0,"condition_time":0,"elif_time":0,"while_time":0,"for_time":0,"call_list":[],"list_handler":[],"class_list":[],"record_condition":[],"eventCounter":0,"Is_code_have_end":False,"In_loop":False,"dync":0})
        return self
    # 获取两数运算结果
    def get_operation(self,num1,num2,operation,func,*args,**kwargs):
        '''运算 返回结果'''
        if(num1 == None or num2==None):
            return 0
        try:
            if isinstance(operation,ast.Add):
                return num1 + num2
            elif isinstance(operation,ast.Sub):
                return num1 - num2
            elif isinstance(operation,ast.Mult):
                return num1 * num2
            elif isinstance(operation,ast.Div):
                return num1 / num2
            elif isinstance(operation,ast.Pow):
                return num1 ** num2
        except:
            return 0
    #
    def py_get_var_info(self,key,arr,func=None,index=-1,*args,**kwargs):
        '''获取 变量信息'''
        for i in arr:
            if i["id"] == key:
                return i
        return None

    def py_get_value(self,key,func=None,index=-1,*args,**kwargs):
        '''获取py记录的堆栈值 变量值'''
        for i in self.stack_frame[index]["data"]:
            if i["id"] == key:
                return i["value"]
        #无
        for i in self.stack_frame[0]["data"]:
            if i["id"] == key:
                return i["value"]
        return None
    def py_get_type(self,key,index=-1,*args,**kwargs):
        '''获取py记录的堆栈值 类型'''
        for i in self.stack_frame[index]["data"]:
            if i["id"] == key:
                return i["type"]
        #无
        for i in self.stack_frame[0]["data"]:
            if i["id"] == key:
                return i["type"]
        return None
    def py_check_type_is_mc(self,key,index=-1,*args,**kwargs):
        '''判断该值类型是否为 系统内置'''
        name = self.py_get_type(key,index,**kwargs)
        if(name in ["MC.ENTITY"]):
            return True
        return False
    def py_return_type_mc(self,key,index=-1,*args,**kwargs):
        '''返回该值类型 系统'''
        name = self.py_get_type(key,index,**kwargs)
        if(self.py_check_type_is_mc(key,index,**kwargs)):
            return name
    # 判断该变量是否为全局变量
    def py_get_value_global(self,key,func:str,index:-1,*args,**kwargs) -> bool:
        '''获取py记录的堆栈值 变量是否为全局变量'''
        for i in self.stack_frame[index]["data"]:
            if i["id"] == key:
                if i.get("is_global")!=None:
                    return i["is_global"]
        #无
        for i in self.stack_frame[0]["data"]:
            if i["id"] == key:
                return True
    # 常量 修改 变量
    def py_change_value(self,key,value,call_mcf:True,func:str,isfundef:False,index:-1,newType="",*args,**kwargs):
        '''
        修改py记录的堆栈值
        常量修改
        isfundef 是否为函数的参数定义
        '''
        NO_exist = True
        is_global = False
        for i in self.stack_frame[index]["data"]:
            if i["id"] == key:
                i["value"] = value
                NO_exist = False
                if(i.get("is_global")==True):
                    for j in self.stack_frame[0]["data"]:
                        if j["id"] == key:
                            j["value"] = value
                            is_global = True
                else:
                    i["is_global"] = False
        if NO_exist:
            self.stack_frame[index]["data"].append({"id":key,"value":value,"type":None,"is_global":False})
        if(call_mcf):
            self.mcf_change_value(key,value,is_global,func,isfundef,index,newType,*args,**kwargs)
        return self
    # 变量 修改 变量
    def py_change_value2(self,key,key2,func:str,isfundef:False,index:-1,newType="",*args,**kwargs):
        '''
        修改py记录的堆栈值
        变量修改
        - isfundef 是否 给函数的参数初始化默认值
        '''
        value = self.py_get_value(key2,func,index)
        NO_exist = True
        is_global = False
        for i in self.stack_frame[index]["data"]:
            if i["id"] == key:
                i["value"] = value
                NO_exist = False
                if(i["is_global"]):
                    for j in self.stack_frame[0]["data"]:
                        if j["id"] == key:
                            j["value"] = value
                            is_global = True
        if NO_exist:
            self.stack_frame[index]["data"].append({"id":key,"value":value})
        self.mcf_change_value2(key,key2,is_global,func,isfundef,index,index,newType,*args,**kwargs)
    # 修改变量的 类型
    def py_change_value_type(self,key,type:str,index=-1,type_check=True,IsChangeMcfData=False,func="",**kwargs):
        '''
        修改py记录的堆栈值的类型
        - type_check 是否对类型进行检查
        '''
        value = type
        if type_check:
            value = self.check_type(type)
        for i in self.stack_frame[index]["data"]:
            if i["id"] == key:
                i["type"] = value
                if(i.get("is_global")==True):
                    for j in self.stack_frame[0]["data"]:
                        if j["id"] == key:
                            i["type"] = value
                else:
                    i["is_global"] = False
        if IsChangeMcfData:
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[{index}].data[{{"id":"{key}"}}].type set value "{value}"\n',**kwargs)
        return self
    # 函数调用参数列表 增加
    def py_call_list_append(self,index:int,value:dict,*args,**kwargs):
        self.stack_frame[index]["call_list"].append(value)
    # 获取函数的参数列表
    def get_function_args(self,key,*args,**kwargs) ->list:
        '''获取函数 参数列表'''
        x = self.get_function_info(key,**kwargs)
        if x != None:
            return x["args"]
        return []
    # 获取函数的调用名称
    def get_function_call_name(self,key,*args,**kwargs) ->str:
        '''获取函数 调回接口函数名称'''
        x = self.get_function_info(key,**kwargs)
        if x != None:
            return x["call"]
        ##非玩家自定义，或还未定义的函数返回默认值
        return "_start"
    # 判断函数是否定义过
    def check_function_exist(self,key,*args,**kwargs) ->str:
        '''判断函数是否存在（即是否已定义）\n用于内置函数判断'''
        x = self.get_function_info(key,**kwargs)
        if x != None:
            return True
        ##非玩家自定义，或还未定义的函数返回默认值
        return False
    # 获取该函数的信息
    def get_function_info(self,key,*args,**kwargs):
        for i in self.stack_frame[0]["functions"]:
            if i["id"] == key:
                return i
        return None

    # 获取class记录的函数列表
    def py_get_class_functions(self,key)->list:
        '''获取py记录的堆栈中 class定义'''
        for i in self.stack_frame[0]["class_list"]:
            if i["id"] == key:
                return i["functions"]
        return None
    # 判断是否定义过该class
    def py_check_class_exist(self,key)->bool:
        '''获取py记录的堆栈中 class是否定义过'''
        for i in self.stack_frame[0]["class_list"]:
            if i["id"] == key:
                return True
        return False
    # Class 函数添加
    def py_get_class_add_function(self,key,value):
        '''获取py记录的堆栈中 class函数添加
        - 自动覆盖
        - value 为 [函数名称,返回值类型,参数列表]
        '''
        if not self.py_check_class_exist(key):
            self.stack_frame[0]["class_list"].append({"id":key,"functions":[]})
        for i in range(len(self.stack_frame[0]["class_list"])):
            if self.stack_frame[0]["class_list"][i]["id"] == key:
                for j in range(len(self.stack_frame[0]["class_list"][i]["functions"])):
                    if self.stack_frame[0]["class_list"][i]["functions"][j]["id"] == value[0]:
                        self.stack_frame[0]["class_list"][i]["functions"][j] = {"id":value[0],"type":value[1],"args":value[2],"from":value[3] if len(value) >=4 else None,"callPath":value[4] if len(value) >=5 else ""}
                        return None
                self.stack_frame[0]["class_list"][i]["functions"].append({"id":value[0],"type":value[1],"args":value[2],"from":value[3] if len(value) >=4 else None,"callPath":value[4] if len(value) >=5 else ""})
                return None
    # 获取该类方法的信息
    def get_class_function_info(self,key,key2,*args,**kwargs):
        '''key类名，key2方法名\n获取类下的方法信息，若不存在则返回None'''
        for i in range(len(self.stack_frame[0]["class_list"])):
            if self.stack_frame[0]["class_list"][i]["id"] == key:
                for j in range(len(self.stack_frame[0]["class_list"][i]["functions"])):
                    if self.stack_frame[0]["class_list"][i]["functions"][j]["id"] == key2:
                        return self.stack_frame[0]["class_list"][i]["functions"][j]
        return None
    # Class 定义函数是否返回
    def GetReturnType(self,tree:ast.FunctionDef,**kwargs) -> str:
        '''判断该函数返回值类型'''
        if isinstance(tree.returns,ast.Constant):
            return tree.returns.value
        if isinstance(tree.returns,ast.Name):
            return tree.returns.id
    # '获取 函数/方法 信息
    def get_func_info(self,className,name,*args,**kwargs):
        '''获取 函数/方法 信息'''
        if className == "" or className == None:
            return self.get_function_info(name,**kwargs)
        else:
            return self.get_class_function_info(className,name,**kwargs)

    # 判断类型
    def check_type(self,item)->str:
        '''类型判断'''
        if isinstance(item,int):
            return "int"
        if isinstance(item,float):
            return "float"
        elif isinstance(item,str):
            # 判断是否自定义类
            if self.py_check_class_exist(item):
                return item
            return "str"
        elif isinstance(item,list):
            return "list"
        else:
            try:
                if item.__name__ == 'MCEntity':
                    return "MC.ENTITY"
            except:
                ...
            return None
    # 判断是否为基本类型
    def check_basic_type(self,item:str)->bool:
        if item in ["int","float","str","list"]: return True
        return False