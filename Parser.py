import ast
import copy
import json
import os
import re
from typing import Callable

import system.mc as mc
from config import custom_functions  # 自定义 函数调用表
from config import defualt_DataPath  # 项目Data文件路径
from config import defualt_NAME  # 项目名称
from config import defualt_PATH  # 默认路径
from config import defualt_STORAGE  # STORAGE
from config import scoreboard_objective  # 默认记分板
from config import system_functions  # 内置 函数调用表
from model.mc_nbt import IntArray, MCNbt, MCStorage, RawJsonText
# from model.mcf_modifier import mcf_modifier
# from model.file_ops import editor_file
from model.py_modifier import py_modifier
from model.DebuggerOut import DebuggerOut
from model.uuid_generator import get_uuid, uuid_to_list
from read_config import read_json

scoreboard_objective2 = scoreboard_objective+'2'

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
    defualt_DataPath = cfg['path'][Pathtime]+"data\\"
    defualt_PATH = cfg['path'][Pathtime]+"data\\"+cfg['name'] + '\\'


class Parser(py_modifier):
    '''解析程序'''
    @update_config_call
    def __init__(self,content,*args,**kwargs) -> None:
        self.code = content
        # 模拟栈 [{  "data":[{"id":"x","value":"","is_global":False},{...}],"is_end":0,"is_return":0,"is_break":0,"is_continue":0,"return":[{"id":"x","value":""}],"type":""  },"exp_operation":[{"value":""}],"functions":[{"id":"","args":[],"call":"","BoolOpTime":0,"Subscript":[{"value":""}]}]]
        # data为记录数据,is_return控制当前函数是否返回,is_end控制该函数是否终止,is_break控制循环是否终止,is_continue是否跳过后续的指令,return 记录调用的函数的返回值 , exp_operation 表达式运算的过程值(栈) is_global 判断该变量是否为全局变量 functions记录函数参数列表,函数调用接口,当前函数 BoolOpTime 条件判断 累计次数 Subscript为记录切片结果 condition_time记录该函数逻辑运算时深度遍历的编号（属于临时变量） "boolOPS"记录逻辑运算的结果 elif_time 记录 elif次数(临时数据) while_time记录 while次数 for_time 记录 for 次数 for_list 记录for迭代的列表([{"value":xx},{..},...]) "call_list" 调用函数的参数列表(  [{"value":"","id":"",is_constant:True}   ]   ,若有id则为kwarg ) , class_list 记录 自定义类的函数与数据 "record_condition" 统计逻辑次数
        #  类型:  BinOp Constant Name BoolOp Compare UnaryOp Subscript list tuple Call Attribute
        self.stack_frame:list[dict] = []
        self.py_append_tree()
        #初始化计分板
        self.write_file('',f'scoreboard objectives add {scoreboard_objective} dummy\n',f2="_init",**kwargs)
        # self.write_file('',f'scoreboard objectives remove {scoreboard_objective2} dummy\n',f2="_init",**kwargs)
        self.write_file('',f'scoreboard objectives add {scoreboard_objective2} dummy\n',f2="_init",**kwargs)
        self.write_file('__main__',f'scoreboard players reset * {scoreboard_objective2}\n',**kwargs)
        self.write_file('__main__',f'#初始化栈与堆\n',**kwargs)
        self.write_file('__main__',f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame set value [{{"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{{}}}}]\n',**kwargs)
        self.write_file('__main__',f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} data set value {{"exp_operation":[],"list_handler":[],"call_list":[],"Subscript":""}}\n',**kwargs)
        self.write_file('__main__',f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} heap set value []\n',**kwargs)
        self.parse('__main__',**kwargs)
    def parse(self,func:str,*args,**kwargs):
        '''func为当前函数的名称'''
        code = copy.deepcopy(self.code)
        code_ = ast.parse(code)
        #遍历python的ast树
        self.walk(code_.body,func,-1,**kwargs)
        print(self.stack_frame)
    def walk(self,tree:list,func:str,index:-1,*args,**kwargs):
        '''遍历AST'''
        kwargs_ = copy.deepcopy(kwargs)
        for item in tree:
            # 赋值
            if isinstance(item,ast.Assign):
                self.Assign(item,func,index,**kwargs)
            # 赋值
            if isinstance(item,ast.AnnAssign):
                self.AnnAssign(item,func,index,**kwargs)
            # 全局化
            elif isinstance(item,ast.Global):
                self.Global(item,func,index,**kwargs)
            # 增强分配+= -= *= /=
            elif isinstance(item,ast.AugAssign):
                self.AugAssign(item,func,index,**kwargs)
            # 函数定义
            elif isinstance(item,ast.FunctionDef):
                self.FunctionDef(item,item.name,index,**kwargs)
            # 类定义
            elif isinstance(item,ast.ClassDef):
                self.ClassDef(item,item.name,index,**kwargs)
            # 函数调用
            elif isinstance(item,ast.Expr):
                
                self.Expr(item,func,index,**kwargs)
            # 函数返回
            elif isinstance(item,ast.Return):
                self.stack_frame[-1]['Is_code_have_end'] = True
                self.Return(item,func,**kwargs)
            # 逻辑运算
            elif isinstance(item,ast.If):
                self.stack_frame[-1]['condition_time'] = 0
                self.stack_frame[-1]['elif_time'] = 0
                self.stack_frame[-1]['BoolOpTime'] += 1
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.end {scoreboard_objective} 0\n',**kwargs)
                self.If(item,self.stack_frame[-1]['condition_time'],func,True,**kwargs)
            # while 循环
            elif isinstance(item,ast.While):
                self.stack_frame[-1]["In_loop"] = True
                self.stack_frame[-1]['BoolOpTime'] += 1
                self.While(item,func,**kwargs)
                self.stack_frame[-1]["In_loop"] = False
            # For 循环 
            elif isinstance(item,ast.For):
                self.stack_frame[-1]["In_loop"] = True
                self.stack_frame[-1]['BoolOpTime'] += 1
                self.For(item,func,**kwargs)
                self.stack_frame[-1]["In_loop"] = False
            # Break 
            elif isinstance(item,ast.Break):
                self.Break(item,func,**kwargs)
            # Continue 
            elif isinstance(item,ast.Continue):
                self.Continue(item,func,**kwargs)
            kwargs = kwargs_

## 工具方法
    # 动态命令
    def build_dynamic_command(self,commands,func,**kwargs):
        ##处理参数

        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list','append',[],func,**kwargs)

        for i in range(len(commands)):
            self.Expr_set_value(ast.Assign(targets=[ast.Name(id=None)],value=commands[i]),func,**kwargs)
        # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].dync','set',{},func,**kwargs)
        for i in range(len(commands)):
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg{i}','set',f'storage {defualt_STORAGE} data.call_list[-1][{i}].value',func,**kwargs)
        self.mcf_call_function(f'{func}/dync_{self.stack_frame[0]["dync"]}/_start with storage {defualt_STORAGE} stack_frame[-1].dync',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].dync','set',{},func,**kwargs)
        self.write_file(func,f'data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
        # 内容
        kwargs['p'] = f'{func}//dync_{self.stack_frame[0]["dync"]}//'
        kwargs['f2'] = f'_start'
        self.write_file(func,f'##    动态命令\n$',inNewFile=True,**kwargs)
        for i in range(len(commands)):
            self.write_file(func,f'$(arg{i})',inNewFile=True,**kwargs)
        self.stack_frame[0]["dync"] += 1
    # 字符串列表转化为动态命令格式
    def list_to_dynamic_command(self,arr,func,**kwargs)->list:
        res = []
        for i in arr:
            res.append(ast.Constant(value=i, kind=None))
        return res
    # mcf动态命令构建
    def mcf_build_dynamic_command(self,inputArgs,runFunction,func,**kwargs):
        '''构造mcf版动态命令
        - inputArgs 为传参列表([storage1,storage2等])
        - runFunction 动态命令列表
        '''
        #动态命令
        self.write_file(func,f'    ##动态命令调用\n',**kwargs)
        for i in range(len(inputArgs)):
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg{i}','set',inputArgs[i],func,**kwargs)
        self.mcf_call_function(f'{func}/dync_{self.stack_frame[0]["dync"]}/_start with storage {defualt_STORAGE} stack_frame[-1].dync',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        self.write_file(func,f'    ##动态命令调用end\n',**kwargs)
        # 内容
        kwargs['p'] = f'{func}//dync_{self.stack_frame[0]["dync"]}//'
        kwargs['f2'] = f'_start'

        self.write_file(func,f'##    动态命令\n',inNewFile=True,**kwargs)
        # 
        for i in runFunction:
            self.write_file(func,i+'\n',inNewFile=True,**kwargs)
        self.stack_frame[0]["dync"] += 1
##

## 赋值
# 赋值
    def Assign(self,tree:ast.Assign,func:str,index:-1,*args,**kwargs):
        '''赋值操作'''
        # 类型扩建TODO
        if isinstance(tree.value,ast.BinOp):
            value = self.preBinOp(tree.value,tree.value.op,func,index,index,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value["value"],False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,value["type"],index,False,True,func,**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[{index}].data[{{"id":"{i.id}"}}].value set {value["data"]}\n',**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',value["data"],func,**kwargs)
                    ClassC.modify_class_var(i,func,tree.value,**kwargs)
                elif isinstance(i,ast.Subscript):
                    x = []
                    def change(storage):
                        storage["value"] = value["value"]
                        storage["type"] = value["type"]
                        return storage
                    def change2(storage,func,kwargs):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage}.value set {value["data"]}\n',**kwargs)
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage}.type set {value["type"]}\n',**kwargs)
                    x.append(change2)
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)
            if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,tree.value.value,True,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,tree.value.value,index,True,True,func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_value(f'{StoragePath}','set',tree.value.value,func,**kwargs)
                    ClassC.modify_class_var(i,func,tree.value.value,**kwargs)
                    ClassC.get_class_var(i,func,**kwargs)['value'] = tree.value.value
                elif isinstance(i,ast.Subscript):
                    x = []
                    def change(storage):
                        storage["value"] = tree.value.value
                        storage["type"] = self.check_type(tree.value.value)
                        return storage
                    x.append(
                        lambda storage,func,kwargs:self.mcf_modify_value_by_value(storage,'set',{"value":tree.value.value,"type":self.check_type(tree.value.value)},func,**kwargs)
                        )
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)

        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value2(i.id,tree.value.id,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,self.py_get_type(tree.value.id,index),index,False,True,func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} stack_frame[{index}].data[{{"id":"{tree.value.id}"}}].value',func,**kwargs)
                    ClassC.modify_class_var(i,func,self.py_get_value(tree.value.id,func,**kwargs),**kwargs)
                elif isinstance(i,ast.Subscript):
                    value = self.py_get_var_info(tree.value.id,self.stack_frame[-1]["data"])
                    x = []
                    def change(storage):
                        storage["value"] = value["value"]
                        storage["type"] = value["type"]
                        return storage
                    def change2(storage,func,kwargs):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage}.value set from storage {defualt_STORAGE} stack_frame[{index}].data[{{"id":"{tree.value.id}"}}]\n',**kwargs)
                    x.append(change2)
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            # 切片赋值
            value = 0
            returnValue = self.preSubscript(tree.value,func,**kwargs)
            storage = returnValue["storage"]
            value = returnValue["value"]
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,None,index,True,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    if(is_global):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[0].data[{{"id":"{i.id}"}}].value set from {storage}\n',**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{i.id}"}}].value set from {storage}\n',**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'{storage}',func,**kwargs)
                    ClassC.modify_class_var(i,func,value,**kwargs)
                elif isinstance(i,ast.Subscript):
                    x = []
                    def change(storage):
                        storage["value"] = returnValue["value"]
                        storage["type"] = returnValue["type"]
                        return storage
                    def change2(storage2,func,kwargs):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage2}.value set from {storage}\n',**kwargs)
                    x.append(change2)
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)
        elif isinstance(tree.value,ast.Call):
            # 函数返回值 赋值
            value = self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # python 赋值 主要是查是否为全局变量
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value['value'],False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,value['type'],index,False,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[0].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
                    ClassC.modify_class_var(i,func,value,**kwargs)
                elif isinstance(i,ast.Subscript):
                    x = []
                    def change(storage):
                        storage["value"] = value["value"]
                        storage["type"] = value["type"]
                        return storage
                    def change2(storage,func,kwargs):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage}.value set from storage {defualt_STORAGE} stack_frame[-1].return[-1].value\n',**kwargs)
                    x.append(change2)
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)
        elif isinstance(tree.value,ast.Attribute):
            # 函数返回值 赋值
            value = self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # if isinstance(value['value'],list) and len(value[0]) >= 2: value = value[0] # 特殊情况 (在获取到 AttributeHandler 中的 inputData)
            # python 赋值 主要是查是否为全局变量
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value['value'],False,func,False,index,**kwargs)
                    
                    self.py_change_value_type(i.id,value['type'],index,False,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[0].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
                    x = ClassC.get_class_var(tree.value,func,**kwargs)
                    ClassC.modify_class_var(i,func,x["value"],**kwargs)
                elif isinstance(i,ast.Subscript):
                    x = []
                    def change(storage):
                        storage["value"] = value["value"]
                        storage["type"] = value["type"]
                        return storage
                    def change2(storage,func,kwargs):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage} set from value {{"value":{value["value"]},"type":{value["type"]}}}\n',**kwargs)
                    x.append(change2)
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)
        elif isinstance(tree.value,ast.BoolOp):
            self.BoolOP_call(tree.value,func,**kwargs)
            # python 赋值 主要是查是否为全局变量
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    #
                    self.py_change_value(i.id,1,False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,1,index,True,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} stack_frame[0].data[{{"id":"{i.id}"}}].value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                    self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} stack_frame[-1].data[{{"id":"{i.id}"}}].value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_change_value_by_scoreboard(f'{StoragePath[8:]}',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                    ClassC.modify_class_var(i,func,1,**kwargs)
                elif isinstance(i,ast.Subscript):
                    x = []
                    def change(storage):
                        storage["value"] = 1
                        storage["type"] = "int"
                        return storage
                    def change2(storage,func,kwargs):
                        self.mcf_change_value_by_scoreboard(storage+'.value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                    x.append(change2)
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)
            self.mcf_old_stack_cover_data(func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Compare):
            self.Compare_call(tree.value,func,**kwargs)
            # python 赋值 主要是查是否为全局变量
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    #
                    self.py_change_value(i.id,1,True,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,1,index,True,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} stack_frame[0].data[{{"id":"{i.id}"}}].value',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{i.id}"}}].value',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_store_value_by_run_command(StoragePath,f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    ClassC.modify_class_var(i,func,1,**kwargs)
                elif isinstance(i,ast.Subscript):
                    x = []
                    def change(storage):
                        storage["value"] = 1
                        storage["type"] = "int"
                        return storage
                    def change2(storage,func,kwargs):
                        self.mcf_change_value_by_scoreboard(storage+'.value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                    x.append(change2)
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)
            self.mcf_old_stack_cover_data(func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.UnaryOp):
            self.UnaryOp_call(tree.value,func,**kwargs)
            # python 赋值 主要是查是否为全局变量
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    #
                    self.py_change_value(i.id,1,True,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,1,index,True,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} stack_frame[0].data[{{"id":"{i.id}"}}].value',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{i.id}"}}].value',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_store_value_by_run_command(StoragePath,f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    ClassC.modify_class_var(i,func,1,**kwargs)
                elif isinstance(i,ast.Subscript):
                    x = []
                    def change(storage):
                        storage["value"] = 1
                        storage["type"] = "int"
                        return storage
                    def change2(storage,func,kwargs):
                        self.mcf_change_value_by_scoreboard(storage+'.value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                    x.append(change2)
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)
            self.mcf_old_stack_cover_data(func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.List):
            value = self.List(tree.value,func,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value["value"],False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,value["type"],index,True,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    if(is_global):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[0].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} data.list_handler\n',**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} data.list_handler\n',**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} data.list_handler',func,**kwargs)
                    ClassC.modify_class_var(i,func,value["value"],**kwargs)
                elif isinstance(i,ast.Subscript):
                    x = []
                    def change(storage):
                        storage["value"] = value["value"]
                        storage["type"] = value["type"]
                        return storage
                    def change2(storage,func,kwargs):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage}.value set from storage {defualt_STORAGE} data.list_handler\n',**kwargs)
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage}.type set from value "list"\n',**kwargs)
                    x.append(change2)
                    x.append(change)
                    returnValue = self.preSubscript(i,func,True,x,**kwargs)
# 类型注解赋值
    def AnnAssign(self,tree:ast.AnnAssign,func:str,index:-1,*args,**kwargs):
        '''带有类型注释的赋值'''
        # tree.annotation
        self.Assign(ast.Assign(targets=[tree.target],value=tree.value),func,index,*args,**kwargs)
        if not isinstance(tree.target,ast.Attribute):
            self.py_change_value_type(tree.target.id,tree.annotation.id,-1,False,True,func,*args,**kwargs)
# 增强分配
    def AugAssign(self,tree:ast.AugAssign,func:str,index:-1,*args,**kwargs):
        '''变量 赋值操作 += -= /= *='''
        # 类型扩建TODO
        if isinstance(tree.value,ast.BinOp):
            value = self.preBinOp(tree.value,tree.value.op,func,index,index,**kwargs)
            i =  tree.target
            if isinstance(i,ast.Name):
                value = self.get_operation(self.py_get_value(i.id,func,index),value["value"],tree.op,func)
                self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} data.exp_operation insert -1 from storage {defualt_STORAGE} stack_frame[{index}].data[{{"id":"{i.id}"}}].value\n',**kwargs)
                self.mcf_change_exp_operation(tree.op,func,self.py_get_type(i.id,func,index),self.check_type(value["type"]),index)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[{index}].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} data.exp_operation[-1].value\n',**kwargs)
            if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            i =tree.target
            if isinstance(i,ast.Name):
                value = tree.value.value
                self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[{index}].temp set value {value}\n',**kwargs)
                self.mcf_change_value_by_operation(i.id,value,self.py_get_value_global(i.id,func,-1),tree.op,func,index,f'storage {defualt_STORAGE} stack_frame[{index}].temp',**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            i = tree.target
            if isinstance(i,ast.Name):
                value = self.get_operation(self.py_get_value(i.id,func,index),self.py_get_value(tree.value.id,func,index),tree.op,func,**kwargs)
                self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                self.mcf_change_value_by_operation(i.id,tree.value.id,self.py_get_value_global(i.id,func,-1),tree.op,func,index,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            # 切片赋值
            returnValue = self.preSubscript(tree.value,func,**kwargs)
            storage = returnValue["storage"]
            value = returnValue["value"]
            i =tree.target
            if isinstance(i,ast.Name):
                self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                is_global = self.py_get_value_global(i.id,func,index,**kwargs)
            # mcf 赋值
                self.mcf_change_value_by_operation2(f'{defualt_STORAGE} stack_frame[-1].data[{{"id":"{i.id}"}}].value',f'{storage}',tree.op,func,-1,**kwargs)
                if(is_global):
                    self.mcf_change_value_by_operation2(f'{defualt_STORAGE} stack_frame[0].data[{{"id":"{i.id}"}}].value',f'{storage}',tree.op,func,-1,**kwargs)
        elif isinstance(tree.value,ast.Call):
            # 函数返回值 赋值
            self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # python 赋值 主要是查是否为全局变量
            value = 0
            i =  tree.target
            if isinstance(i,ast.Name):
                self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                is_global = self.py_get_value_global(i.id,func,index,**kwargs)
            # mcf 赋值
                self.mcf_change_value_by_operation2(f'{defualt_STORAGE} stack_frame[-1].data[{{"id":"{i.id}"}}].value',f'{defualt_STORAGE} stack_frame[-1].return[-1].value',tree.op,func,-1,**kwargs)
                if(is_global):
                    self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} stack_frame[0].data[{{"id":"{i.id}"}}].value',f'#{defualt_NAME}.sys.temp1 {scoreboard_objective}','double',0.001,func,**kwargs)
## Global
    def Global(self,tree:ast.Global,func:str,index:-1,*args,**kwargs):
        '''Global 全局变量 '''
        for i in tree.names:
            for j in self.stack_frame[0]["data"]:
                if j["id"] == i:
                    self.stack_frame[index]["data"].append({"id":i,"value":j["value"],"is_global":True})
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[{index}].data[{{"id":"{j["id"]}"}}].value set from storage {defualt_STORAGE} stack_frame[0].data[{{"id":{j["id"]}}}].value\n',**kwargs)

## 运算调用前置
    def preBinOp(self,tree:ast.BinOp,op:ast.operator,func:str,index:-1,index2:-1,time=0,*args,**kwargs) -> dict:
        value = self.BinOp(tree,op,func,index,index2,time,**kwargs)
        returnValue = value.value
        data = f'from storage {defualt_STORAGE} data.exp_operation[-1].value'
        isConstant = False
        if (value.kind == None) or (value.kind[0] == "have_operation"):
            #常数获取类型
            returnType = self.check_type(value.value)
            data = f'value {returnValue}'
            isConstant = True
        else:
            #变量等获取类型
            returnType = value.kind[1]
        return {"value":returnValue,"type":returnType,"data":data,"isConstant":isConstant}

# 运算
    def BinOp(self,tree:ast.BinOp,op:ast.operator,func:str,index:-1,index2:-1,time=0,*args,**kwargs) -> ast.Constant:
        '''运算操作
        tree新的树，op操作类型 +-*/
        time 处理常量运算
        调用完后，并且处理完返回值，需 移除计算数据 （如果返回的值为非常数）
        >>> self.mcf_remove_Last_exp_operation(func,**kwargs)
        '''
        # 类型扩建TODO
        ##判断左右值
        if isinstance(tree.left,ast.BinOp):
            tree.left = self.BinOp(tree.left,tree.left.op,func,index,index2,time+1,**kwargs)
        if isinstance(tree.right,ast.BinOp):
            tree.right = self.BinOp(tree.right,tree.right.op,func,index,index2,time+1,**kwargs)
        tree_list:ast = [tree.left,tree.right]
        for item in range(2):
            
            # 假如为变量
            if isinstance(tree_list[item],ast.Name):
                value = self.py_get_value(tree_list[item].id,func,index,**kwargs)
                # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.exp_operation','append',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree_list[item].id}"}}]',func,**kwargs)
                tree_list[item] = ast.Constant(value=value, kind=["is_v",self.py_get_type(tree_list[item].id,index),tree_list[item].id,tree_list[item]])
            # 假如为函数返回值
            elif isinstance(tree_list[item],ast.Call):
                # 函数返回值 赋值
                value = self.Expr(ast.Expr(value=tree_list[item]),func,-1,*args,**kwargs)
                # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.exp_operation','append',f'storage {defualt_STORAGE} stack_frame[-1].return[-1]',func,**kwargs)
                tree_list[item] = ast.Constant(value=value['value'], kind=["is_call",value['type']])
            elif isinstance(tree_list[item],ast.Subscript):
                # 切片赋值
                returnValue = self.preSubscript(tree_list[item],func,**kwargs)
                storage = returnValue["storage"]
                value = returnValue["value"]
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.exp_operation[-1].value','set',f'{storage}',func,**kwargs)
                tree_list[item] = ast.Constant(value=value, kind=["is_call",None])
            elif isinstance(tree_list[item],ast.Attribute):
                # 属性
                ClassC = ClassCall(self.stack_frame,**kwargs)
                StoragePath = ClassC.class_var_to_str(tree_list[item],func,**kwargs)
                value = ClassC.get_class_var(tree_list[item],func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.exp_operation','append',StoragePath[0:-6],func,**kwargs)
                # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                tree_list[item] = ast.Constant(value=value.get('value'), kind=["is_v",value.get('type')])
        tree.left,tree.right = (tree_list[0],tree_list[1])
        # 常量处理
        if isinstance(tree.left,ast.Constant) and isinstance(tree.right,ast.Constant):
            ## mcf 处理
            if (tree.left.kind == None) and (tree.right.kind == None ):
                #常量
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                # if not time:
                    #
                    # self.mcf_add_exp_operation(value,func,index,**kwargs)
                return ast.Constant(value=value, kind=["have_operation",self.check_type(value)])
            # have_operation标记没有涉及到变量的 常量之间的运算
            elif (tree.left.kind != None and tree.left.kind[0] == "have_operation" and tree.left.kind[1] != None) and (tree.right.kind != None and tree.right.kind[0] == "have_operation" and tree.right.kind[1] != None):
                # 涉及到 已经运算过的式子的之间的运算（）
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                # if not time:
                    # self.mcf_add_exp_operation(value,func,index,**kwargs)
                return ast.Constant(value=value, kind=["have_operation",self.check_type(value)])
            elif (tree.left.kind != None and tree.left.kind[0] == "have_operation" and tree.left.kind[1] != None) and (tree.right.kind == None):
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                # if not time:
                    # self.mcf_add_exp_operation(value,func,index,**kwargs)
                return ast.Constant(value=value, kind=["have_operation",self.check_type(value)])
            elif (tree.left.kind == None) and (tree.right.kind != None and tree.right.kind[0] == "have_operation" and tree.right.kind[1] != None):
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                # if not time:
                    # self.mcf_add_exp_operation(value,func,index,**kwargs)
                return ast.Constant(value=value, kind=["have_operation",self.check_type(value)])
            # 涉及到变量
            else:
                #受变量影响的值
                if (tree.left.kind == None or tree.left.kind[0]=="have_operation"):
                    self.mcf_add_exp_operation(tree.left.value,func,index,**kwargs)
                if (tree.right.kind == None or tree.right.kind[0]=="have_operation"):
                    self.mcf_add_exp_operation(tree.right.value,func,index,**kwargs)
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                type1 = tree.left.kind[1] if tree.left.kind != None else self.check_type(tree.left.value)
                type2 = tree.right.kind[1] if tree.right.kind != None else self.check_type(tree.right.value)
                # 魔术方法
                if not self.check_basic_type(type1):
                    sign = None
                    if isinstance(op,ast.Add) and self.get_class_function_info(type1,"__add__"): sign = '__add__'
                    if isinstance(op,ast.Sub) and self.get_class_function_info(type1,"__sub__"): sign = '__sub__'
                    if isinstance(op,ast.Mult) and self.get_class_function_info(type1,"__mul__"): sign = '__mul__'
                    if isinstance(op,ast.Div) and self.get_class_function_info(type1,"__truediv__"): sign = '__truediv__'
                    def call():
                        mmh = MagicMethodHandler(self.stack_frame)
                        # 传参
                        inputArgs = [
                            f"storage {defualt_STORAGE} data.exp_operation[-1]"
                            ]
                        value = mmh.main(None,tree.left.kind[1],sign,func,inputArgs,storage=f"storage {defualt_STORAGE} stack_frame[{index-1}].exp_operation[-2].value",**kwargs)
                        self.write_file(func,f'''execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} data.exp_operation[-1] set from storage {defualt_STORAGE} stack_frame[{index}].return[-1]\n''',**kwargs)
                        self.write_file(func,f'''execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} data.exp_operation[-2]\n''',**kwargs)
                        return ast.Constant(value=value['value'], kind=['is_v',value['type'],None])
                    if sign != None: return call()
                self.mcf_change_exp_operation(op,func,index,type1,type2,**kwargs)
                return ast.Constant(value=value, kind=['is_v',self.check_type(value)])
# 函数定义
    def FunctionDef(self,tree:ast.FunctionDef,func:str,index:-1,*args,**kwargs):
        '''函数定义'''
        kwargs['Is_new_function'] = True
        Return_type = self.GetReturnType(tree,**kwargs)

        #如果是类函数则添加进类数据中
        self.py_append_tree()
        if not kwargs.get("ClassName"):
            callpath = defualt_NAME+":"+func+"/_start"
            self.stack_frame[0]["functions"].append({"id":func,"args":[],"call":"_start","type":Return_type,"callPath":callpath})
        #读取函数参数
        args_list = []
        for item in tree.args.args:
            if isinstance(item,ast.arg):
                if not kwargs.get("ClassName"):
                    self.stack_frame[0]["functions"][-1]["args"].append(item.arg)
                args_list.append(item.arg)
        if kwargs.get("ClassName"):
            callpath = defualt_NAME+":"+kwargs.get("ClassName")+"/"+func+"/_start"
            self.py_get_class_add_function(kwargs.get("ClassName"),[func,Return_type,args_list,None,callpath])
        #装饰器处理器
        if tree.decorator_list:
            for i in tree.decorator_list:
                DH = DecoratoHandler(self.stack_frame)
                self.stack_frame = DH.main(i,func,**kwargs)
        #
        if kwargs.get("f2"):
            kwargs.pop("f2")
        f2 = "_start"
        if self.get_func_info(kwargs.get("ClassName"),func,**kwargs).get("cached"):
            f2 = "_start2"
        
        # 函数注解
        if tree.body and \
            (isinstance(tree.body[0],ast.Expr) and
            isinstance(tree.body[0].value,ast.Constant) and
            isinstance(tree.body[0].value.value,str)):
                for i in tree.body[0].value.value.split("\n"):
                    self.write_file(func,f'#{i}\n',f2='_start',**kwargs)

        #函数参数初始化
        self.write_file(func,f'##函数参数初始化\n',f2=f2,**kwargs)
        self.FunctionDef_args_init(tree.args,args_list,func,index,f2=f2,**kwargs)
        #

        
        self.write_file(func,f'##函数主体\n',f2=f2,**kwargs)
        
        self.walk(tree.body,func,index,f2=f2,**kwargs)
        # 如果无返回，则返回字符串None
        if not self.stack_frame[-1]['Is_code_have_end']:
            self.Return(ast.Return(value=ast.Constant(value="None", kind=None)),func,f2=f2,**kwargs)
        self.write_file(func,f'##函数结尾\n',f2=f2,**kwargs)
        if f2 == "_start2":
            funcName = f'{func}/_start2'
            self.mcf_call_function(funcName,func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1.. run ',**kwargs)
        # 若该函数为缓存函数，则存储返回结果
        if f2 == "_start2":
            # 内容
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg0','set',f'storage {defualt_STORAGE} stack_frame[-1].key',func,**kwargs)
            self.mcf_call_function(f'{func}/dync_{self.stack_frame[0]["dync"]}/_start with storage {defualt_STORAGE} stack_frame[-1].dync',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1.. run ',**kwargs)
            kwargs['p'] = f'{func}//dync_{self.stack_frame[0]["dync"]}//'
            CachedData = f'storage {defualt_STORAGE} stack_frame[0].CachedFunctions[{{"id":"{func}"}}].value.\'$(arg0)\''
            if kwargs.get("ClassName"):
                CachedData = f'storage {defualt_STORAGE} stack_frame[0].CachedMethod[{{"id":"{kwargs.get("ClassName")}"}}].value[{{"id":"{func}"}}].value.\'$(arg0)\''
            if not self.stack_frame[-1]['Is_code_have_end']:
                self.write_file(func,f'##    动态命令\n$data modify {CachedData} set value {{"value":"None"}}\n',inNewFile=True,**kwargs)
            else:
                self.write_file(func,f'##    动态命令\n$data modify {CachedData} set from storage {defualt_STORAGE} stack_frame[-2].return[-1]\n',inNewFile=True,**kwargs)
            # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].dync','set',{},func,**kwargs)
            
            self.stack_frame[0]["dync"] += 1
        self.stack_frame.pop(-1)
# 函数参数处理 参数预先值
    def FunctionDef_args_init(self,tree:ast.arguments,args_list:list,func:str,index:-1,*args,**kwargs):
        '''函数定义中 参数预先值'''
        # 类型扩建TODO
        for i in range(-1,-1*len(tree.defaults)-1,-1):
            if isinstance(tree.defaults[i],ast.BinOp):
                value = self.preBinOp(tree.defaults[i],tree.defaults[i].op,func,index,index-1,**kwargs)
                self.py_change_value(args_list[i],value["value"],False,func,False,index,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute unless data storage {defualt_STORAGE} stack_frame[{index}].data[{{"id":"{args_list[i]}"}}] run data modify storage {defualt_STORAGE} stack_frame[{index}].data[{{"id":"{args_list[i]}"}}].value set {value["data"]}\n',**kwargs)
                if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
            elif isinstance(tree.defaults[i],ast.Constant):
                # 常数赋值
                self.py_change_value(args_list[i],tree.defaults[i].value,True,func,True,index,**kwargs)
            elif isinstance(tree.defaults[i],ast.Name):
                # 变量赋值
                self.py_change_value2(args_list[i],tree.defaults[i].id,func,True,index,**kwargs)

# 表达式调用
    def Expr(self,tree:ast.Expr,func:str,index:-1,loopTime=0,*args,**kwargs):
        '''函数调用 处理'''
        func_name = '' #函数名称
        Call = tree.value
        
        if isinstance(Call , ast.Call):
            if isinstance(Call.func , ast.Name):
                func_name = Call.func.id
                #函数参数赋值
                args = self.get_function_args(func_name,**kwargs)
                call_name = self.get_function_call_name(func_name,**kwargs)
                self.write_file(func,f'\n##    调用函数\n',**kwargs)
                self.write_file(func,f'#参数处理\n',**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list','append',[],func,**kwargs)
                self.stack_frame[-1]["call_list"] = []
                #位置传参
                for i in range(len(Call.args)):
                    self.Expr_set_value(ast.Assign(targets=[ast.Name(id=None)],value=Call.args[i]),func,**kwargs)
                #关键字传参
                for i in range(len(Call.keywords)):
                    if isinstance(Call.keywords[i],ast.keyword):
                        self.Expr_set_value(ast.Assign(targets=[ast.Name(id=Call.keywords[i].arg)],value=Call.keywords[i].value),func,**kwargs)
                self.mcf_new_stack(func,**kwargs)

                # if(len(Call.args)!=0 or len(Call.keywords) != 0):
                    # self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.call_list','set',f'storage {defualt_STORAGE} data.call_list',func,**kwargs)
                ## 优先判断该函数是否已存在，若未存在，即可能为类实例化
                if self.check_function_exist(func_name,**kwargs):
                    ## mcf
                    self.write_file(func,f'#参数处理.赋值\n',**kwargs)
                    #位置传参
                    for i in range(len(args)):
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{args[i]}"}}].value','set',f'storage {defualt_STORAGE} data.call_list[-1][{i}].value',func,**kwargs)
                    #关键字传参
                    for i in range(len(Call.keywords)):
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{Call.keywords[i].arg}"}}].value','set',f'storage {defualt_STORAGE} data.call_list[-1][{{"id":{Call.keywords[i].arg}}}].value',func,**kwargs)
                    self.write_file(func,f'#函数调用\n',**kwargs)
                    getprefix = self.get_func_info("",func_name,**kwargs).get("prefix")
                    prefix = f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run "+getprefix if getprefix != None else f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run "
                    self.mcf_call_function(f'{func_name}/{call_name}',func,prefix=prefix,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
                    self.write_file(func,f'##  调用结束\n',**kwargs)
                else:
                    self.write_file(func,f'#内置函数or类实例化调用\n',**kwargs)
                    self.stack_frame[-1]["call_list"] = Call.args
                    SF = System_function(self.stack_frame,func_name,func,**kwargs)
                    x = SF.main(**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
                    self.write_file(func,f'##  调用结束\n',**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
                    return x
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
                if not kwargs.get("ClassName"):
                    for i in self.stack_frame[0]["functions"]:
                        if i["id"] == func_name:
                            return {"value":None,"type":i["type"]}
                return {"value":None,"type":None}
            elif isinstance(Call.func,ast.Attribute):
                
                ## 属性处理
                attribute_name = None
                if isinstance(Call.func.value,ast.Name):
                    attribute_name = Call.func.value.id
                func_name = Call.func.attr
                
                #函数参数赋值
                args = self.get_function_args(func_name,**kwargs)
                call_name = self.get_function_call_name(func_name,**kwargs)
                if(attribute_name!='mc' and not self.py_check_type_is_mc(attribute_name)): #可能为自定义类的方法调用
                    
                    self.write_file(func,f'\n##函数调用_begin (自定义类的方法调用)\n',**kwargs)
                    self.write_file(func,f'#参数处理.函数处理\n',**kwargs)
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list','append',[],func,**kwargs)
                    self.stack_frame[-1]["call_list"] = []
                    #位置传参
                    for i in range(len(Call.args)):
                        self.Expr_set_value(ast.Assign(targets=[ast.Name(id=None)],value=Call.args[i]),func,**kwargs)
                    #关键字传参
                    for i in range(len(Call.keywords)):
                        if isinstance(Call.keywords[i],ast.keyword):
                            self.Expr_set_value(ast.Assign(targets=[ast.Name(id=Call.keywords[i].arg)],value=Call.keywords[i].value),func,**kwargs)
                    self.mcf_new_stack(func,**kwargs)
                    #判断是否为第三方数据包
                    SF = Custom_function(self.stack_frame,attribute_name,func_name,**kwargs)
                    x = {"value":None,"type":None}
                    result = {"value":None,"type":None}
                    if not SF.main(func,**kwargs):
                        self.stack_frame[-1]["call_list"] = Call.args
                        x:dict = self.AttributeHandler(Call.func,func,True,**kwargs)
                        self.stack_frame[-1]["call_list"] = Call.args
                        if x.get('ReturnValue'):
                            try:
                                
                                Handler = TypeAttributeHandler(self.stack_frame,x['ReturnValue']["value"],x['ReturnValue']["type"],func_name,None,True,storage = x['inputData'])
                                result = Handler.main(func,**kwargs)
                            except:
                                ...
                        elif x.get("haveCallFunc"):
                            result = x
                            # result = x
                        else:
                            Handler = TypeAttributeHandler(self.stack_frame,x.get('value'),self.check_type(x.get('value')),func_name,None,True)
                            x = Handler.main(func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
                    return result
                else:
                    ## mc内置
                    self.stack_frame[-1]["call_list"] = Call.args
                    MCF =  mc_function(self.stack_frame)
                    x = MCF.main(func_name,self.stack_frame[-1]["call_list"],func,attribute_name=self.py_return_type_mc(attribute_name),var=attribute_name,**kwargs)
                    return x
        elif isinstance(Call , ast.Attribute):
            #属性 (类)
            self.mcf_new_stack(func,**kwargs)
            x = {"value":None,"type":None}
            if not isinstance(Call.value,ast.Call):
                x = {"value":None,"type":None}
                
                try:
                    Handler = TypeAttributeHandler(
                        self.stack_frame,
                        self.py_get_value(Call.value.id,-1,**kwargs),
                        self.py_get_type(Call.value.id,-1,**kwargs),Call.attr,None,False
                        )
                    x = Handler.main(func,True,**kwargs)
                except:
                    ...
                
                if x == {"value":None,"type":None}:
                    # 说明是获取的为变量
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(Call,func,**kwargs)
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].return','append',{"value":0,"type":"num"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value','set',f'{StoragePath}',func,**kwargs)
                    x = ClassC.get_class_var(Call,func,**kwargs)
                    x = {"value":x.get('value'),"type":x.get('type')}
                else:
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].return','append',{"value":x[0],"type":f"{x[1]}"},func,**kwargs)
            else:
                x:dict = self.AttributeHandler(Call,func,False,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].return','append',{"value":0,"type":"num"},func,**kwargs)
                
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value','set',f'{x[1].replace("return[-1]","return[-2]")}',func,**kwargs)
            # self.mcf_remove_stack_data(func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
            # self.mcf_remove_stack_data(func,**kwargs)
            return x
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
        
        return {"value":None,"type":None}
# 调用函数时 参数处理器
    def Expr_set_value(self,tree:ast.Assign,func,loopTime=0,*args,**kwargs):
        '''函数调用 传参\n
        参数处理'''
        # 类型扩建TODO
        if isinstance(tree.value,ast.BinOp):
            value = self.preBinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_call_list_append(-1,{"value":value["value"],"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} data.call_list[-1][-1].value set {value["data"]}\n',**kwargs)
            if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_call_list_append(-1,{"value":tree.value.value,"id":i.id,"is_constant":True})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list[-1]','append',{"value":tree.value.value,"id":f"{i.id}"},func,**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_call_list_append(-1,{"value":self.py_get_value(tree.value.id,func,False,-1,**kwargs),"id":i.id,"is_constant":False},**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.call_list[-1]','append',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.value.id}"}}]',func,**kwargs)
        elif isinstance(tree.value,ast.BoolOp):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    #
                    self.stack_frame[-1]['condition_time'] += 1
                    self.mcf_new_stack(func,**kwargs)
                    self.mcf_new_stack_inherit_data(func,**kwargs)
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                    kwargs_ = copy.deepcopy(kwargs)
                    kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
                    kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
                    kwargs['Is_new_function'] = False
                    self.BoolOp(tree.value,0,func,True,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                    self.BoolOp_operation(tree.value,0,0,func,**kwargs)
                    kwargs = kwargs_
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} data.call_list[-1][-1].value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Compare):
            self.Compare_call(tree.value,func,**kwargs)
            # python 赋值 主要是查是否为全局变量
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} data.call_list[-1][-1].value','int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.UnaryOp):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.mcf_new_stack(func,**kwargs)
                    self.mcf_new_stack_inherit_data(func,**kwargs)
                    self.stack_frame[-1]['condition_time'] += 1
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                    self.UnaryOp(tree.value,True,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                    self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} data.call_list[-1][-1].value','int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    returnValue =  self.preSubscript(tree.value,func,**kwargs)
                    storage = returnValue["storage"]
                    value = returnValue["value"]
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.call_list[-1][-1].value','set',f'{storage}',func,**kwargs)
        elif isinstance(tree.value,ast.Call):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    # 函数返回值 赋值
                    self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.call_list[-1][-1].value','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
        elif isinstance(tree.value,ast.Attribute):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    ClassC = ClassCall(self.stack_frame,**kwargs)
                    StoragePath = ClassC.class_var_to_str(tree.value,func,**kwargs)
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.call_list[-1][-1].value','set',f'{StoragePath}',func,**kwargs)
        elif isinstance(tree.value,ast.List):
            self.List(tree.value,func,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.call_list[-1][-1].value','set',f'storage {defualt_STORAGE} data.list_handler',func,**kwargs)
# 返回值
    def Return(self,tree:ast.Return,func,*args,**kwargs):
        '''函数返回值处理'''
        # 类型扩建TODO
        self.write_file(func,f'##函数返回值处理_bengin\n',**kwargs)
        if isinstance(tree.value,ast.BinOp):
            value = self.preBinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
            if len(self.stack_frame) >=2:
                self.stack_frame[-2]['return'].append(value["value"])
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} stack_frame[-2].return[-1].value set {value["data"]}\n',**kwargs)
            if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            if len(self.stack_frame) >=2:
                self.stack_frame[-2]['return'].append(tree.value.value)
            value = tree.value.value
            if isinstance(value,str):
                value = "\""+str(value)+"\""
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].return append value {{"value":{value}}}\n',**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            if len(self.stack_frame) >=2:
                self.stack_frame[-2]['return'].append(self.py_get_value(tree.value.id,func,-1))
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} stack_frame[-2].return[-1].value set from storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.value.id}"}}].value\n',**kwargs)
        elif isinstance(tree.value,ast.Call):
            value = self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            if len(self.stack_frame) >=2:
                self.stack_frame[-2]['return'].append(self.py_get_value(value['value'],func,-1))
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].return append from storage {defualt_STORAGE} stack_frame[-1].return[-1]\n',**kwargs)
        elif isinstance(tree.value,ast.BoolOp):
            self.BoolOP_call(tree.value,func,**kwargs)
            #
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-3].return','append',{"value":0},func,**kwargs)
            self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} stack_frame[-3].return[-1].value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
            if len(self.stack_frame) >=2:
                self.stack_frame[-2]['return'].append(0)
        elif isinstance(tree.value,ast.Compare):
            self.Compare_call(tree.value,func,**kwargs)
            #
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-3].return','append',{"value":0},func,**kwargs)
            self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} stack_frame[-3].return[-1].value','int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.UnaryOp):
            self.mcf_new_stack(func,**kwargs)
            self.mcf_new_stack_inherit_data(func,**kwargs)
            self.stack_frame[-1]['condition_time'] += 1
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            self.UnaryOp(tree.value,True,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
            #
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-3].return','append',{"value":0},func,**kwargs)
            self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} stack_frame[-3].return[-1].value','int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            if len(self.stack_frame) >=2:
                self.stack_frame[-2]['return'].append(0)
            returnValue =  self.preSubscript(tree.value,func,**kwargs)
            storage = returnValue["storage"]
            value = returnValue["value"]
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-2].return','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-2].return[-1].value','set',f'{storage}',func,**kwargs)
        self.mcf_stack_return(func,**kwargs)
        self.write_file(func,f'##函数返回值处理_end\n',**kwargs)
# 切片处理前置
    def preSubscript(self,tree:ast.Subscript,func,isAssign=False,Assignfunc=None,*args,**kwargs):
        '''isAssign:是否为赋值,\n若为赋值则传入赋值函数\nAssignfunc赋值函数修改strage数值,类型;py数值,类型'''
        if not isAssign:
            pretext = f'$data modify storage {defualt_STORAGE} data.Subscript set from'
            returnValue =  self.Subscript(tree,func,0,**kwargs)
            self.write_file(func,f'    ##动态命令调用\n',**kwargs)
            self.mcf_call_function(f'{func}/dync_{self.stack_frame[0]["dync"]}/_start with storage {defualt_STORAGE} stack_frame[-1].dync',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
            self.write_file(func,f'    ##动态命令调用end\n',**kwargs)
            # 内容
            kwargs['p'] = f'{func}//dync_{self.stack_frame[0]["dync"]}//'
            kwargs['f2'] = f'_start'
            self.write_file(func,f'##    动态命令\n',inNewFile=True,**kwargs)
            #
            self.write_file(func,f'{pretext} {returnValue[0]}\n',**kwargs)
            #
            self.stack_frame[0]["dync"] += 1
            #
            return {"storage":f'storage {defualt_STORAGE} data.Subscript',"value":returnValue[1]["value"],"type":returnValue[1]["type"]}
        else:
            returnValue =  self.Subscript(tree,func,0,**kwargs)
            self.write_file(func,f'    ##动态命令调用\n',**kwargs)
            self.mcf_call_function(f'{func}/dync_{self.stack_frame[0]["dync"]}/_start with storage {defualt_STORAGE} stack_frame[-1].dync',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
            self.write_file(func,f'    ##动态命令调用end\n',**kwargs)
            # 内容
            kwargs['p'] = f'{func}//dync_{self.stack_frame[0]["dync"]}//'
            kwargs['f2'] = f'_start'
            self.write_file(func,f'##    动态命令\n',inNewFile=True,**kwargs)
            #
            self.write_file(func,f'$',inNewFile=True,**kwargs)

            Assignfunc[0](returnValue[0][0:-6],func,kwargs)
            returnValue[3] = self.change_listVar_by_index(returnValue[3],returnValue[2],Assignfunc[1])
            self.stack_frame[0]["dync"] += 1
            #
            return {"storage":returnValue[0],"value":returnValue[1]["value"],"type":returnValue[1]["type"]}
# 切片 (列表或字典)
    def Subscript(self,tree:ast.Subscript,func,loop_time=0,*args,**kwargs):
        '''切片处理\n返回 (storage,value)'''
        # 类型扩建TODO
        if isinstance(tree.value,ast.Subscript):
            returnValue =  self.Subscript(tree.value,func,loop_time+1,**kwargs)
            indexs = returnValue[2]
            indexs.append(
                self.Subscript_index(tree.slice,func,loop_time,**kwargs)
            )
            return [returnValue[0]+f'[$(arg{loop_time})].value',returnValue[1],indexs,returnValue[3]]
        else:
            if isinstance(tree.value,ast.Call):
                # 函数返回值
                returnValue = self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
                self.Subscript_index(tree.slice,func,loop_time,**kwargs)
                return [f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value[$(arg{loop_time})].value',returnValue,[index],returnValue["value"]]
            elif isinstance(tree.value,ast.Name):
                # 变量
                index = self.Subscript_index(tree.slice,func,loop_time,**kwargs)
                value = None
                valueType = None
                return [f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":{tree.value.id}}}].value[$(arg{loop_time})].value',{"value":value,"type":valueType},[index],self.py_get_value(tree.value.id,func)]
            elif isinstance(tree.value,ast.BinOp):
                # 运算
                self.Subscript_index(tree.slice,func,loop_time,**kwargs)
                value = self.preBinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
                self.write_file(func,f'data modify storage {defualt_STORAGE} stack_frame[-1].Subscript2 set value {value["data"]}\n',**kwargs)
                if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
                return [f'storage {defualt_STORAGE} stack_frame[-1].Subscript2[$(arg{loop_time})].value',{"value":0,"type":None},[index],value["value"]]


            elif isinstance(tree.value,ast.Constant):
                self.Subscript_index(tree.slice,func,loop_time,**kwargs)
                return [f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":{tree.value.value}}}].value[$(arg{loop_time})].value',{"value":0,"type":None},[index],self.py_get_value(tree.value.value,func)]
            elif isinstance(tree.value,ast.List):
                returnValue = self.List(tree.value,func,**kwargs)
                self.Subscript_index(tree.slice,func,loop_time,**kwargs)
                return [f'storage {defualt_STORAGE} data.list_handler[$(arg{loop_time})].value',returnValue,[index],returnValue["value"]]

# 切片指针处理器 (列表或字典)
    def Subscript_index(self,tree:ast.Index,func,loop_time=0,*args,**kwargs):
        # 类型扩建TODO
        # 直接构建动态命令参数
        if isinstance(tree.value,ast.Subscript):
            returnValue =  self.preSubscript(tree.value,func,**kwargs)
            storage = returnValue["storage"]
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg{loop_time}','set',storage,func,**kwargs)
            return returnValue["value"]
        elif isinstance(tree.value,ast.Name):
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg{loop_time}','set',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":{tree.value.id}}}].value',func,**kwargs)
            index = self.py_get_value(tree.value.id,func)
            return index
        elif isinstance(tree.value,ast.Call):
            self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg{loop_time}','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
        elif isinstance(tree.value,ast.BinOp):
            returnValue = self.preBinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg{loop_time}','set',returnValue["data"],func,**kwargs)
            if not returnValue["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
            return returnValue["value"]
        elif isinstance(tree.value,ast.Constant):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg{loop_time}','set',tree.value.value,func,**kwargs)
            return tree.value.value
        elif isinstance(tree.value,ast.List):
            returnValue = self.List(tree.value,func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg{loop_time}','set',f'storage {defualt_STORAGE} data.list_handler',func,**kwargs)
            return returnValue["value"]


## 逻辑模块
# if
    def If(self,tree:ast.If,condition_time:0,func:str,mode:True,*args,**kwargs):
        '''
        逻辑运算 if elif else\n
        mode 为 判断当前是否为if模式 True为If,False为elif
        '''
            #test
        only_test = False
        for key, value in kwargs.items():
            if((key=='only_test') and value == True):
                only_test = True
        kwargs_ = copy.deepcopy(kwargs)
        #重置 “统计逻辑条件”
        self.stack_frame[-1]["record_condition"] = []
        if mode:
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/call',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.end {scoreboard_objective} matches 0 run ',**kwargs)
            kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
        else:
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/call',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.end {scoreboard_objective} matches 0 run ',**kwargs)
            kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//'
        kwargs['f2'] = f'call'
        kwargs['Is_new_function'] = False
        self.write_file(func,f'#\n',**kwargs)
        # 类型扩建TODO
        if isinstance(tree.test,ast.BoolOp):
            self.stack_frame[-1]['condition_time'] += 1
            if mode:
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
                kwargs['Is_new_function'] = False
                self.BoolOp(tree.test,condition_time+1,func,mode,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.BoolOp_operation(tree.test,1,0,func,**kwargs)
                
            else:
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)

                kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//'
                kwargs['Is_new_function'] = False
                
                self.BoolOp(tree.test,condition_time+1,func,False,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.BoolOp_operation(tree.test,1,0,func,**kwargs)
        if isinstance(tree.test,ast.BinOp):
            self.stack_frame[-1]['condition_time'] += 1
            if mode:
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
                kwargs['Is_new_function'] = False
                value = self.preBinOp(tree.test,tree.test.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',value["data"],func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)

                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
            else:
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//'
                kwargs['Is_new_function'] = False
                value = self.preBinOp(tree.test,tree.test.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',value["data"],func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)

                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.test,ast.Compare):
            self.stack_frame[-1]['condition_time'] += 1
            if mode:
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                self.Compare(tree.test,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            else:
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                self.Compare(tree.test,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
        elif isinstance(tree.test,ast.UnaryOp):
            self.stack_frame[-1]['condition_time'] += 1
            if mode:
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                self.UnaryOp(tree.test,mode,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}')
                self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
            else:
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                self.UnaryOp(tree.test,mode,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
        elif isinstance(tree.test,ast.Name):
            self.stack_frame[-1]['condition_time'] += 1

            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.test.id}"}}].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Call):
            self.stack_frame[-1]['condition_time'] += 1
            self.Expr(ast.Expr(value=tree.test),func,-1,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].return[-1].value\n',**kwargs)
        elif isinstance(tree.test,ast.Attribute):
            ClassC = ClassCall(self.stack_frame,**kwargs)
            StoragePath = ClassC.class_var_to_str(tree.test,func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get {StoragePath}\n',**kwargs)
        elif isinstance(tree.test,ast.Constant):
            self.stack_frame[-1]['condition_time'] += 1
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":tree.test.value},func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Subscript):
            self.stack_frame[-1]['condition_time'] += 1
            returnValue =  self.preSubscript(tree.test,func,**kwargs)
            storage = returnValue["storage"]
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'{storage}',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        #body
        kwargs = copy.deepcopy(kwargs_)
        self.write_file(func,f'#\n',**kwargs)
        if not only_test:
            if mode:
                #调用
                kwargs['ClassName'] = kwargs.get("ClassName")
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run ',**kwargs)
                # end if
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.end {scoreboard_objective} 1\n',p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'main',ClassName=kwargs.get("ClassName"))
                kwargs['Is_new_function'] = False
                self.walk(tree.body,func,-1,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'main',ClassName=kwargs.get("ClassName"))
            else:
                #调用
                kwargs['ClassName'] = kwargs.get("ClassName")
                self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run ',**kwargs)
                # end if
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.end {scoreboard_objective} 1\n',p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'main',ClassName=kwargs.get("ClassName"))
                kwargs['Is_new_function'] = False
                self.walk(tree.body,func,-1,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'main',ClassName=kwargs.get("ClassName"))
            if len(tree.orelse) >0:
                kwargs = kwargs_
                if isinstance(tree.orelse[0],ast.If) and len(tree.orelse) ==1:
                #elif
                    kwargs['ClassName'] = kwargs.get("ClassName")
                    self.stack_frame[-1]['elif_time'] += 1
                    self.stack_frame[-1]['condition_time'] = 0
                    self.If(tree.orelse[0],0,func,False,ClassName=kwargs.get("ClassName"),**kwargs)
                else:
                    kwargs['ClassName'] = kwargs.get("ClassName")
                    self.write_file(func,f'#\n',**kwargs)
                        #调用 else
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/else/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 run ',**kwargs)
                    # kwargs['Is_new_function'] = False
                    self.walk(tree.orelse,func,-1,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//else//',f2=f'main',ClassName=kwargs.get("ClassName"))

# 布尔运算
    def BoolOp(self,tree:ast.BoolOp,condition_time:0,func:str,mode:bool = True,*args,**kwargs):
        '''逻辑运算 and or \n mode为else'''
        for item in tree.values:
            # 类型扩建TODO
            if isinstance(item,ast.BoolOp):
                self.stack_frame[-1]['condition_time'] += 1
                if mode:
                    
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_operation(item,self.stack_frame[-1]["condition_time"],condition_time,func,**kwargs)
                    self.BoolOp(item,self.stack_frame[-1]["condition_time"],func,mode,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_operation(item,self.stack_frame[-1]["condition_time"],condition_time,func,**kwargs)
                    self.BoolOp(item,condition_time,func,mode,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            elif isinstance(item,ast.Compare):
                self.stack_frame[-1]['condition_time'] += 1
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_record(tree,condition_time,self.stack_frame[-1]["condition_time"],func,**kwargs)
                    self.Compare(item,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                    
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_record(tree,condition_time,self.stack_frame[-1]["condition_time"],func,**kwargs)
                    self.Compare(item,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            elif isinstance(item,ast.UnaryOp):
                self.stack_frame[-1]['condition_time'] += 1
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_record(tree,condition_time,self.stack_frame[-1]["condition_time"],func,**kwargs)
                    self.UnaryOp(item,mode,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_record(tree,condition_time,self.stack_frame[-1]["condition_time"],func,**kwargs)
                    self.UnaryOp(item,mode,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            elif isinstance(item,ast.Name):
                self.stack_frame[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.stack_frame[-1]["condition_time"]}'
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.stack_frame[-1]["condition_time"]}'
                
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{item.id}"}}].value',func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run scoreboard players operation #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} = #{defualt_NAME}.sys.c.{condition_time}.pass {scoreboard_objective}\n',**kwargs)
                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.stack_frame[-1]["condition_time"],func,**kwargs)
            elif isinstance(item,ast.Constant):
                self.stack_frame[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.stack_frame[-1]["condition_time"]}'
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.stack_frame[-1]["condition_time"]}'
                
                self.mcf_reset_score(f'#{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective}',func,**kwargs)
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} {item.value}\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective} 1\n',**kwargs)
                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.stack_frame[-1]["condition_time"],func,**kwargs)
            elif isinstance(item,ast.BinOp):
                self.stack_frame[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.stack_frame[-1]["condition_time"]}'
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.stack_frame[-1]["condition_time"]}'
                
                value = self.preBinOp(item,item.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',value["data"],func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.stack_frame[-1]["condition_time"],func,**kwargs)
                if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
            elif isinstance(item,ast.Subscript):
                self.stack_frame[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.stack_frame[-1]["condition_time"]}'
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/elif_{self.stack_frame[-1]["elif_time"]}/{self.stack_frame[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.stack_frame[-1]["condition_time"]}'
                
                returnValue =  self.preSubscript(item,func,**kwargs)
                storage = returnValue["storage"]
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'{storage}',func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)

                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.stack_frame[-1]["condition_time"],func,**kwargs)
# 比较
    def Compare(self,tree:ast.Compare,condition_time:0,func:str,*args,**kwargs):
        '''判断语句 > < == != >= <='''
        #左
        # 类型扩建TODO
        if isinstance(tree.left,ast.BinOp):
            value = self.preBinOp(tree.left,tree.left.op,func,-1,-1,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',value["data"],func,**kwargs)
            if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.left,ast.Constant):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":tree.left.value},func,**kwargs)
        elif isinstance(tree.left,ast.Name):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.left.id}"}}].value',func,**kwargs)
        elif isinstance(tree.left,ast.Call):
            # 函数返回值 赋值
            self.Expr(ast.Expr(value=tree.left),func,-1,**kwargs)
            # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',f'storage {defualt_STORAGE} stack_frame[-1].return[-1]',func,**kwargs)
        #右
        # 类型扩建TODO
        for item in tree.comparators:
            if isinstance(item,ast.BinOp):
                value = self.preBinOp(item,item.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',value["data"],func,**kwargs)
                if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
            elif isinstance(item,ast.Constant):
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":item.value},func,**kwargs)
            elif isinstance(item,ast.Name):
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.left.id}"}}].value',func,**kwargs)
            elif isinstance(item,ast.Call):
            # 函数返回值 赋值
                self.Expr(ast.Expr(value=item),func,-1,**kwargs)
                # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
        #再根据判断类型 > < >= <= != ==
        for item in tree.ops:
            if isinstance(item,ast.cmpop):
                self.mcf_reset_score(f'#{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective}',func,**kwargs)
                self.mcf_compare_Svalues(f'{defualt_STORAGE} stack_frame[-1].boolOPS[-2].value',f'{defualt_STORAGE} stack_frame[-1].boolOPS[-1].value',item,func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective} 1',**kwargs)
# 布尔 and/or
    def BoolOp_operation(self,tree:ast.BoolOp,condition_time:int,condition_time2:int,func:str,*args,**kwargs):
        '''逻辑运算中 and or'''
        if isinstance(tree.op,ast.And):
            self.write_file(func,f'##和\nscoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\nexecute if score #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} = #{defualt_NAME}.sys.c3.{condition_time} {scoreboard_objective2} run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            #
        elif isinstance(tree.op,ast.Or):
            self.write_file(func,f'##或\nscoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\nexecute if score #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
# 记录 运算后的布尔值
    def BoolOp_record(self,tree:ast.BoolOp,condition_time:int,index:int,func:str,*args,**kwargs):
        '''逻辑运算中 记录逻辑结果'''

        #统计该情况下的所有逻辑判断
        
        # 判断是否初始化过
        flag = self.BoolOp_check_has_init(condition_time,func,**kwargs)
        if not flag:
            self.write_file(func,f'scoreboard players add #{defualt_NAME}.sys.c3.{condition_time} {scoreboard_objective2} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{index} {scoreboard_objective} matches 1 run scoreboard players add #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} 1\n',**kwargs)
        else:
            pre = ''
            if isinstance(tree.op,ast.And):
                pre = f'execute unless score #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} = #{defualt_NAME}.sys.c3.{condition_time} {scoreboard_objective2} run '
            elif isinstance(tree.op,ast.Or):
                pre = f'execute unless score #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} matches 1.. run '
            self.write_file(func,f'{pre}scoreboard players add #{defualt_NAME}.sys.c3.{condition_time} {scoreboard_objective2} 1\n',**kwargs)
            self.write_file(func,f'{pre}execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{index} {scoreboard_objective} matches 1 run scoreboard players add #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} 1\n',**kwargs)

    def BoolOp_check_has_init(self,condition_time,func,*args,**kwargs)->bool:
        '''判断是否已经初始化'''
        if not(condition_time in self.stack_frame[-1]["record_condition"]):
            self.stack_frame[-1]["record_condition"].append(condition_time)
            self.write_file(func,f'#@ 初始化 逻辑统计记分板\nscoreboard players set #{defualt_NAME}.sys.c3.{condition_time} {scoreboard_objective2} 0\nscoreboard players set #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} 0\n##\n',**kwargs)
            return False
        return True

    def BoolOp_get_prefix(self,tree:ast.BoolOp,condition_time,func,*args,**kwargs)->str:
        '''若已初始化，则直接获得（"或"的熔断）的前缀'''
        # 判断是否初始化过
        pre = ''
        if self.BoolOp_check_has_init(condition_time,func,**kwargs):
            if isinstance(tree.op,ast.Or):
                pre = f'execute unless score #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} matches 1.. run '
        return pre
# 逻辑调用

    def BoolOP_call(self,value:ast.boolop,func:str,*args,**kwargs):
        """boolop调用\n
        返回 处理scoreboard #{defualt_NAME}.sys.c.0.pass {scoreboard_objective}"""
        self.stack_frame[-1]['condition_time'] += 1
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
        kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
        kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
        kwargs['Is_new_function'] = False
        self.BoolOp(value,0,func,True,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
        self.BoolOp_operation(value,0,0,func,**kwargs)

    def Compare_call(self,value:ast.Compare,func:str,*args,**kwargs):
        """Compare调用\n
        返回处理\n 
        self.mcf_store_value_by_run_command(f'{}','int 1'f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
        """
        self.stack_frame[-1]['condition_time'] += 1
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
        self.Compare(value,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
        self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
        

    def UnaryOp_call(self,value:ast.UnaryOp,func:str,*args,**kwargs):
        """UnaryOp调用"""
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.stack_frame[-1]['condition_time'] += 1
        self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
        self.UnaryOp(value,True,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
        self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)

##

# 一元操作(目前有：取反)
    def UnaryOp(self,tree:ast.UnaryOp,mode:bool,condition_time:0,func:str,*args,**kwargs):
        '''条件 一元运算符 '''
        self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        # self.If(ast.If(test=tree.operand,body=[],orelse=[]),condition_time,func,mode,only_test=True,**kwargs)
        ## 取反
        # 类型扩建TODO
        if isinstance(tree.operand,ast.BoolOp):
            if mode:
                kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
                kwargs['Is_new_function'] = False
                self.BoolOp(tree.operand,condition_time+1,func,mode,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.BoolOp_operation(tree.operand,0,0,func,**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//'
                kwargs['Is_new_function'] = False
                
                self.BoolOp(tree.operand,condition_time+1,func,False,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.BoolOp_operation(tree.operand,0,0,func,**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
        if isinstance(tree.operand,ast.BinOp):
            if mode:
                kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
                kwargs['Is_new_function'] = False
                value = self.preBinOp(tree.operand,tree.operand.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',value["data"],func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//'
                kwargs['Is_new_function'] = False
                value = self.preBinOp(tree.operand,tree.operand.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',value["data"],func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Compare):
            if mode:
                self.Compare(tree.operand,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                self.Compare(tree.operand,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.UnaryOp):
            if mode:
                self.UnaryOp(tree.operand,mode,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                self.UnaryOp(tree.operand,mode,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//elif_{self.stack_frame[-1]["elif_time"]}//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                #取反
                self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Name):

            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.operand.id}"}}].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)

            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            #取反
            self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Constant):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":tree.operand.value},func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            #取反
            self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Subscript):
            returnValue =  self.preSubscript(tree.operand,func,**kwargs)
            storage = returnValue["storage"]
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'{storage}',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            #取反
            self.get_condition_reverse(func,**kwargs)
# 条件取反
    def get_condition_reverse(self,func,*args,**kwargs):
        '''条件取反'''
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass_ {scoreboard_objective} 0\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass_ {scoreboard_objective} 1\n',**kwargs)
        self.mcf_reset_score(f'#{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective}',func,**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run scoreboard players operation #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass_ {scoreboard_objective}\n',**kwargs)

## 循环模块
# while
    def While(self,tree:ast.While,func:str,*args,**kwargs):
        '''While循环处理'''
        self.stack_frame[-1]["while_time"] += 1
        # test
        ## while前 新建栈
        self.write_file(func,f'     ##while_begin   \n',**kwargs)
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.mcf_call_function(f'{func}/while_{self.stack_frame[-1]["while_time"]}/_start',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        self.mcf_old_stack_cover_data(func,**kwargs)
        self.mcf_remove_stack_data(func,**kwargs)
        self.write_file(func,f'     ##while_end     \n',**kwargs)

        kwargs_ = copy.deepcopy(kwargs)
        kwargs['Is_new_function'] = False
        kwargs['p'] = f'{func}//while_{self.stack_frame[-1]["while_time"]}//'
        kwargs['f2'] = f'_start'
        ## is_continue
        self.write_file(func,f'execute if data storage {defualt_STORAGE} stack_frame[-1].is_continue run scoreboard players reset #{defualt_STORAGE}.stack.end {scoreboard_objective}\n',**kwargs)
        self.write_file(func,f'execute if data storage {defualt_STORAGE} stack_frame[-1].is_continue run data remove storage {defualt_STORAGE} stack_frame[-1].is_continue\n',**kwargs)
        #
        self.mcf_call_function(f'{func}/while_{self.stack_frame[-1]["while_time"]}/condition/_start',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        

        kwargs['p'] = f'{func}//while_{self.stack_frame[-1]["while_time"]}//condition//'
        # 类型扩建TODO
        if isinstance(tree.test,ast.Name):
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.stack_frame[-1]['condition_time'] = 0
            self.stack_frame[-1]['condition_time'] += 1
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.test.id}"}}].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)

            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Call):
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.stack_frame[-1]['condition_time'] = 0
            self.stack_frame[-1]['condition_time'] += 1
            self.Expr(ast.Expr(value=tree.test),func,-1,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].return[-1].value\n',**kwargs)

        elif isinstance(tree.test,ast.UnaryOp):
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.stack_frame[-1]['condition_time'] = 1
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            self.UnaryOp(tree.test,True,self.stack_frame[-1]["condition_time"],func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.{self.stack_frame[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
        elif isinstance(tree.test,ast.Constant):
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.stack_frame[-1]['condition_time'] = 0
            self.stack_frame[-1]['condition_time'] += 1
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":tree.test.value},func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)

            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Compare):
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.stack_frame[-1]['condition_time'] = 0
            self.Compare_call(tree.test,func,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            self.stack_frame[-1]['condition_time'] = 0
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.test,ast.BoolOp):
            self.stack_frame[-1]['condition_time'] = 0
            self.stack_frame[-1]['condition_time'] += 1
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            self.BoolOp(tree.test,1,func,True,p=f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//',f2=f'{self.stack_frame[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            self.BoolOp_operation(tree.test,0,0,func,**kwargs)
            self.stack_frame[-1]['condition_time'] = 0
        elif isinstance(tree.test,ast.Subscript):
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.stack_frame[-1]['condition_time'] += 1
            returnValue =  self.preSubscript(tree.test,func,**kwargs)
            storage = returnValue["storage"]
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',f'{storage}',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.BinOp):
            self.stack_frame[-1]['condition_time'] += 1
            self.mcf_call_function(f'{func}/condition_{(self.stack_frame[-1]["BoolOpTime"])}/if/{self.stack_frame[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.stack_frame[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.stack_frame[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            value = self.preBinOp(tree.test,tree.test.op,func,-1,-1,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value','set',value["data"],func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} stack_frame[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
        # body
        kwargs['p'] = f'{func}//while_{self.stack_frame[-1]["while_time"]}//'
        kwargs['f2'] = f'_start'
        self.write_file(func,f'##while 主程序\n',**kwargs)

        self.mcf_call_function(f'{func}/while_{self.stack_frame[-1]["while_time"]}/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run ',**kwargs)
        temp_value = self.stack_frame[-1]["while_time"]
        self.walk(tree.body,func,-1,p=f'{func}//while_{self.stack_frame[-1]["while_time"]}//',f2=f'main',ClassName=kwargs.get("ClassName"))

        self.mcf_call_function(f'{func}/while_{temp_value}/_start',func,p=f'{func}//while_{temp_value}//',f2=f'main',ClassName=kwargs.get("ClassName"))
# break
    def Break(self,tree:ast.Break,func,*args,**kwargs):
        '''Break 处理'''
        self.write_file(func,f'     # Break\n',**kwargs)
        self.mcf_stack_break(func,**kwargs)
# continue
    def Continue(self,tree:ast.Continue,func,*args,**kwargs):
        '''Continue 处理'''
        self.write_file(func,f'     # Continue\n',**kwargs)
        self.mcf_stack_continue(func,**kwargs)
# for
    def For(self,tree:ast.For,func:str,*args,**kwargs):
        '''for循环 处理'''
        self.stack_frame[-1]["for_time"] += 1
        
        # test
        ## for前 新建栈
        
        self.write_file(func,f'    ##for_begin   \n',**kwargs)
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.mcf_call_function(f'{func}/for_{self.stack_frame[-1]["for_time"]}/_start',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        self.mcf_old_stack_cover_data(func,**kwargs)
        self.mcf_remove_stack_data(func,**kwargs)
        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].data[{{"temp":1b}}]','remove','',func,**kwargs)
        self.write_file(func,f'    ##for_end     \n',**kwargs)

        kwargs_ = copy.deepcopy(kwargs)

        kwargs['Is_new_function'] = False
        kwargs['p'] = f'{func}//for_{self.stack_frame[-1]["for_time"]}//'
        kwargs['f2'] = f'_start'
        ##初始化 迭代器列表
        self.write_file(func,f'#迭代器初始化\n',**kwargs)
        self.mcf_call_function(f'{func}/for_{self.stack_frame[-1]["for_time"]}/iterator/_init',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        ## is_continue
        kwargs['f2'] = f'main'
        self.write_file(func,f'execute if data storage {defualt_STORAGE} stack_frame[-1].is_continue run scoreboard players reset #{defualt_STORAGE}.stack.end {scoreboard_objective}\n',**kwargs)
        self.write_file(func,f'execute if data storage {defualt_STORAGE} stack_frame[-1].is_continue run data remove storage {defualt_STORAGE} stack_frame[-1].is_continue\n',**kwargs)
        #
        self.mcf_call_function(f'{func}/for_{self.stack_frame[-1]["for_time"]}/iterator/_start',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        kwargs['p'] = f'{func}//for_{self.stack_frame[-1]["for_time"]}//iterator//'
        if isinstance(tree.target,ast.Name):
            kwargs['f2'] = f'_start'
            kwargs['p'] = f'{func}//for_{self.stack_frame[-1]["for_time"]}//iterator//'
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.target.id}","temp":1b}}].value','set',f'storage {defualt_STORAGE} stack_frame[-1].for_list[0].value',func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].for_list[0]','remove','',func,**kwargs)
            if isinstance(tree.iter,ast.Call):
                kwargs['f2'] = f'_init'
                kwargs['p'] = f'{func}//for_{self.stack_frame[-1]["for_time"]}//iterator//'
                # 函数返回值 赋值
                self.Expr(ast.Expr(value=tree.iter),func,-1,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].for_list','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)

        # body
        kwargs['p'] = f'{func}//for_{self.stack_frame[-1]["for_time"]}//'
        kwargs['f2'] = f'_start'
        self.write_file(func,f'##for 主程序\n',**kwargs)
        self.mcf_call_function(f'{func}/for_{self.stack_frame[-1]["for_time"]}/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        temp_value = self.stack_frame[-1]["for_time"]
        ## 
        
        self.walk(tree.body,func,-1,p=f'{func}//for_{self.stack_frame[-1]["for_time"]}//',f2=f'main',ClassName=kwargs.get("ClassName"))
        self.mcf_call_function(f'{func}/for_{temp_value}/main',func,p=f'{func}//for_{temp_value}//',f2=f'main',ClassName=kwargs.get("ClassName"),prefix = f'execute if data storage {defualt_STORAGE} stack_frame[-1].for_list[0] run ')
        ##

##

# list
    def List(self,tree:ast.List,func:str,loop_time=0,*args,**kwargs):
        ''''列表 处理'''
        var_list = [] #存储到编译器的值（主要是类型）
        if loop_time==0:
            # 重置
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler','set',[],func,**kwargs)
        if len(tree.elts) == 0:
            # 空列表
            var_list.append({"value":[],"type":"list"})
            text = '[-1]'*(loop_time)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',[],func,**kwargs)
            return {"value":var_list,"type":"list"}
        for item in tree.elts:
            #子数据
            text = '[-1].value'*(loop_time)
            text2 = '[-1].value'*(loop_time+1)
            if isinstance(item,ast.BinOp):
                value = self.preBinOp(item,item.op,func,-1,-1,**kwargs)
                var_list.append({"value":value["value"],"type":value["type"]})
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',{"value":"None"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.list_handler{text2}','set',value["data"],func,**kwargs)
                if not value["isConstant"]: self.mcf_remove_Last_exp_operation(func,**kwargs)
            elif isinstance(item,ast.Constant):
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',{"value":item.value},func,**kwargs)
                var_list.append({"value":item.value,"type":self.check_type(item.value)})
            elif isinstance(item,ast.Name):
                self.py_get_value(item.id,func,-1,**kwargs)
                var_list.append({"value":self.py_get_value(item.id),"type":self.py_get_type(item.id)})
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',{"value":"None"},func,**kwargs)
                IsGlobal = self.py_get_value_global(item.id,func,-1,**kwargs)
                if IsGlobal:
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.list_handler{text2}','set',f'storage {defualt_STORAGE} stack_frame[0].data[{{"id":"{item.id}"}}].value',func,**kwargs)
                else:
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.list_handler{text2}','set',f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{item.id}"}}].value',func,**kwargs)
            elif isinstance(item,ast.Subscript):
                # 切片赋值
                returnValue =  self.preSubscript(item,func,**kwargs)
                storage = returnValue["storage"]
                var_list.append({"value":returnValue["value"],"type":returnValue["type"]})
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',{"value":"None"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.list_handler{text2}','set',f'{storage}',func,**kwargs)
            elif isinstance(item,ast.Call):
                # 函数返回值 赋值
                returnValue = self.Expr(ast.Expr(value=item),func,-1,**kwargs)
                # python 赋值 主要是查是否为全局变量
                # self.stack_frame[-1]["list_handler"].append(None)
                var_list.append({"value":returnValue["value"],"type":returnValue["type"]})

                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',{"value":"None"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.list_handler{text2}','set',f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value',func,**kwargs)
            elif isinstance(item,ast.BoolOp):
                self.BoolOP_call(item,func,**kwargs)
                # python 赋值 主要是查是否为全局变量
                var_list.append({"value":0,"type":"int"})
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',{"value":"None"},func,**kwargs)
                self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} data.list_handler{text2}',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                self.mcf_remove_stack_data(func,**kwargs)
            elif isinstance(item,ast.Compare):
                self.Compare_call(item,func,**kwargs)
                var_list.append({"value":0,"type":"int"})
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',{"value":"None"},func,**kwargs)
                self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} data.list_handler{text2}',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                self.mcf_remove_stack_data(func,**kwargs)
            elif isinstance(item,ast.UnaryOp):
                self.UnaryOp_call(item,func,**kwargs)
                var_list.append({"value":0,"type":"int"})
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',{"value":"None"},func,**kwargs)
                self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} data.list_handler{text2}',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.stack_frame[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                self.mcf_remove_stack_data(func,**kwargs)
            elif isinstance(item,ast.List):
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.list_handler{text}','append',{"value":[]},func,**kwargs)
                x = self.List(item,func,loop_time+1,**kwargs)
                var_list.append({"value":x.get('value'),"type":x.get('type')})
        return {"value":var_list,"type":"list"}
# 属性处理
    def AttributeHandler(self,tree:ast.Attribute,func:str,IsCallFuc=False,inputData='',*args,**kwargs):
        '''属性处理
        IsCallFuc=False:调用属性的值
        IsCallFuc=True:为调用属性方法
        '''
        
        ReturnValue= {"value":None,"type":None}
        
        if isinstance(tree.value,ast.Attribute):
            ReturnData = self.AttributeHandler(tree.value,func,False,**kwargs)
            print("6666 ",ReturnData)
            ReturnValue = ReturnData.get('ReturnValue')
            inputData = ReturnData.get(inputData)
            if not IsCallFuc:
                ReturnValue = self.py_get_var_info(tree.attr,ReturnData['ReturnData']["value"])
                inputData += f'[{{"id":"{tree.attr}"}}].value'
            return {"value":None,"type":None,"ReturnValue":ReturnValue,"inputData":inputData}

        elif isinstance(tree.value,ast.Call):
            if not IsCallFuc:
                inputData = f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value[{{"id":"{tree.attr}"}}].value'
            else:
                inputData = f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value'
            ReturnValue = self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # if len(ReturnValue) > 2 and ReturnValue[2].get("selfVar"): inputData = ReturnValue[2].get("selfVar")
            
            return {"value":ReturnValue.get('value'),"type":ReturnValue.get('type'),"ReturnValue":ReturnValue,"inputData":inputData}
        elif isinstance(tree.value,ast.Name):
            # 查类型
            # 根据 类型 调用属性
            if not IsCallFuc:
                inputData = f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.value.id}"}}].value[{{"id":"{tree.attr}"}}].value'
                x = self.py_get_var_info(tree.value.id,self.stack_frame[-1]["data"])
                ReturnValue= {"value":None,"type":None,"ReturnValue":None,"inputData":inputData}
                ReturnValue['value'] = self.py_get_var_info(tree.attr,x["value"])
                ClassC = ClassCall(self.stack_frame,**kwargs)
                var = ClassC.get_class_var(tree,func,**kwargs)
                value = var.get('value')
                type = var.get('type')
                return {"value":None,"type":None,"ReturnValue":None,"inputData":inputData}
            if IsCallFuc:
                var = self.py_get_var_info(tree.value.id,self.stack_frame[0]["data"])
                ##判断是否为类的名称
                if var == None:
                    var = {"id":tree.value.id,"type":None,"value":None}
                    for i in self.stack_frame[0]["class_list"]:
                        if i["id"] == tree.value.id:
                            var = {"id":tree.value.id,"type":i["id"],"value":None}
                
                Handler = TypeAttributeHandler(self.stack_frame,var["value"],var["type"],tree.attr,var["id"],IsCallFuc)
                ReturnValue:list = Handler.main(func,**kwargs)
                ReturnValue["newName"] = tree.attr

        # else:
        #     Handler = TypeAttributeHandler(self.stack_frame,ReturnValue[0],self.check_type(ReturnValue[1]),tree.attr,None,IsCallFuc)
        #     ReturnValue = Handler.main(func,**kwargs)
        if not IsCallFuc:
            if not isinstance(tree.value,(ast.Name,ast.Call)):
                Handler = TypeAttributeHandler(self.stack_frame,ReturnValue[0],self.check_type(ReturnValue[1]),tree.attr,None,IsCallFuc)
                ReturnValue = Handler.main(func,**kwargs)
        
        return ReturnValue

# 类的定义
    def ClassDef(self,tree:ast.ClassDef,func:str,index:-1,*args,**kwargs):
        '''类的定义'''
        self.stack_frame[0]["class_list"].append({"id":tree.name,"functions":[]})
        kwargs["ClassName"]=tree.name
        kwargs["f2"] = "_start"
        kwargs["p"] = f''
        #继承
        for item in tree.bases:
            if isinstance(item,ast.Name):
                if self.py_check_class_exist(item.id):
                    for i in self.py_get_class_functions(item.id):
                        self.py_get_class_add_function(tree.name,[i['id'],i['type'],i['args'],item.id])
                else:
                    DebuggerOut("父类未定义",[__file__.system._getframe().f_lineno-4],True)
        #
        
        self.walk(tree.body,func,index,**kwargs)


# python内置函数处理器
class System_function(Parser):
    '''内置函数 处理器'''
    def __init__(self,*args,**kwargs) -> None:
        '''storage名称 nbt'''
        if len(args) >= 3:
            self.stack_frame,self.func_name,self.func = tuple(args[0:3])
    def main(self,*args,**kwargs):
        if self.func_name == 'print':
            return self._print(self.func,**kwargs)

        elif self.func_name == 'range':
            return self._range(self.func,**kwargs)
        elif self.func_name == 'str':
            return self._str(self.func,**kwargs)
        elif self.func_name == 'isinstance':
            return self._isinstance(self.func,**kwargs)
        else:
            # 自定义函数
            IsFind = False
            for item in system_functions:
                if item['name'] == self.func_name:
                    self.write_file(self.func,f'#参数处理.赋值\n',**kwargs)
                    for i in range(len(item['args'])):
                        if item['args'][i]['type'] == 'storage':
                            self.write_file(self.func,f"data modify storage {item['args'][i]['name']} set from storage {defualt_STORAGE} data.call_list[-1][{i}].value\n",**kwargs)
                    self.write_file(self.func,f'#自定义函数调用\n',**kwargs)
                    self.write_file(self.func,f"function {item['call_path']}\n",**kwargs)
                    if item['return']['type'] == 'storage':
                            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-2].return','append',{"value":0},self.func,**kwargs)
                            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-2].return[-1].value','set',f"storage {item['return']['name']}",self.func,**kwargs)
                    IsFind = True
            if not IsFind:
                #如果没找到对应的函数名称，则可能为类的调用
                ClassC = ClassCall(self.stack_frame,self.func_name,**kwargs)
                return ClassC.init(self.func,**kwargs)
            else:
                return {"value":None,"type":None}

    def _print(self,func,*args,**kwargs):
        self.write_file(func,f'#参数处理.赋值\n',**kwargs)
        self.write_file(func,f'#自定义函数调用\n',**kwargs)
        text = f'tellraw @a ['

        def baseType(text,texti): # 基本类型处理
            value = RawJsonText(MCStorage('storage',f'{defualt_STORAGE}',f'data.call_list[-1][{i}].value'))
            text += str(value)
            if i >= 0 and i < len(self.stack_frame[-1]["call_list"]) - 1:
                text += '," ",'
            return text

        def addText(text,i,value):
            text += str(value)
            if i >= 0 and i < len(self.stack_frame[-1]["call_list"]) - 1:
                text += '," ",'
            return text

        for i in range(len(self.stack_frame[-1]["call_list"])):
            #判断是否存在魔术方法
            if isinstance(self.stack_frame[-1]["call_list"][i],ast.Name):
                # 获取变量的类型
                varName = self.stack_frame[-1]["call_list"][i].id
                varType = self.py_get_type(varName,-1,*args,**kwargs)
                if self.check_basic_type(varType): #判断是否为基本类型
                    text = baseType(text,i)
                    continue
                if self.get_class_function_info(varType,"__str__"): #判断是否存在 __str__ 方法
                    mmh = MagicMethodHandler(self.stack_frame)
                    # 传参
                    inputArgs = []
                    mmh.main(None,varType,"__str__",func,inputArgs,storage=f'storage {defualt_STORAGE} data.call_list[-2][{i}].value',**kwargs)
                    value = RawJsonText(MCStorage('storage',f'{defualt_STORAGE}',f'stack_frame[-1].return[-1].value'))
                else:
                    value = f'{{"text":" < 类名:{varType} 变量名:{varName} > "}}'
                text = addText(text,i,value)
            else:
                text = baseType(text,i)
        text += ']\n'
        self.write_file(func,f'{text}',func,**kwargs)

        self.write_file(func,f'##函数调用_end\n',**kwargs)
    def _range(self,func,*args,**kwargs):
        self.write_file(func,f'#参数处理.赋值\n',**kwargs)
        self.write_file(func,f'#自定义函数调用\n',**kwargs)
        handle = True
        range_list = []
        for i in self.stack_frame[-1]["call_list"]:
            if isinstance(i,ast.Constant):
                range_list.append(i.value)
        if len(range_list) < 2:
            handle = False
        mcf_range_list = []
        if handle:
            for i in range(*range_list):
                mcf_range_list.append({"value":i})
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-2].return','append',{"value":0},self.func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-2].return[-1].value','set',mcf_range_list,self.func,**kwargs)
        else:
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage t_algorithm_lib:array range.input set from storage {defualt_STORAGE} data.call_list[-1][0].value\n',**kwargs)
            self.write_file(func,f'function t_algorithm_lib:array/range/start\n',**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-2].return','append',{"value":0},self.func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-2].return[-1].value','set',[],**kwargs)
        self.write_file(func,f'##函数调用_end\n',**kwargs)
        return {"value":mcf_range_list,"type":"list"}
    def _str(self,func,*args,**kwargs):

        # 判断是否存在魔术方法
        if isinstance(self.stack_frame[-1]["call_list"][0],ast.Name):
            # 获取变量的类型
            varName = self.stack_frame[-1]["call_list"][0].id
            varType = self.py_get_type(varName,-1,*args,**kwargs)
            if self.get_class_function_info(varType,"__str__"): #判断是否存在 __str__ 方法
                mmh = MagicMethodHandler(self.stack_frame)
                # 传参
                inputArgs = []
                value = mmh.main(varName,varType,"__str__",func,inputArgs,storage=None,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-2].return','append',f'storage {defualt_STORAGE} stack_frame[-1].return[-1]',self.func,**kwargs)
                return value
        #
        self.write_file(func,f'#自定义函数调用\n',**kwargs)
        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-2].return','append',{"value":"None"},self.func,**kwargs)

        self.mcf_build_dynamic_command(
            [f'storage {defualt_STORAGE} data.call_list[-1][-1].value'],
            [f'$data modify storage {defualt_STORAGE} stack_frame[-2].return[-1].value set value \'$(arg0)\''],
            func,**kwargs)
        self.write_file(func,f'##函数调用_end\n',**kwargs)

        # self.write_file(func,f'data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
        
        return {"value":"","type":"str"}
    def _isinstance(self,func,*args,**kwargs):
        if not len(self.stack_frame[-1]["call_list"]) >= 2:
            # self.write_file(func,f'data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
            return {"value":1,"type":"int"}
        # 
        storage = ''
        if isinstance(self.stack_frame[-1]["call_list"][0],ast.Name):
            storage = f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{self.stack_frame[-1]["call_list"][0].id}"}}].type'
        elif isinstance(self.stack_frame[-1]["call_list"][0],ast.Attribute):
            ClassC = ClassCall(self.stack_frame,**kwargs)
            storage = ClassC.class_var_to_str(i,func,**kwargs)[0:-5] + '.type'
        classList = []
        for i in self.stack_frame[-1]["call_list"][1:]:
            if isinstance(i,ast.Constant):
                classList.append(i.value)
            elif isinstance(i,ast.Name):
                classList.append(i.id)
        
        self.write_file(func,f'scoreboard players set #{defualt_STORAGE}.stack.t {scoreboard_objective} {len(classList)}\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].temp set value {classList}\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 store result score #{defualt_STORAGE}.stack.t2 {scoreboard_objective} run data modify storage {defualt_STORAGE} stack_frame[-2].temp[] set from {storage}\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].return append value {{"value":0}}\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute unless score #{defualt_STORAGE}.stack.t {scoreboard_objective} = #{defualt_STORAGE}.stack.t2 {scoreboard_objective} run data modify storage {defualt_STORAGE} stack_frame[-2].return[-1].value set value 1\n',**kwargs)

        # self.write_file(func,f'data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
        
        return {"value":1,"type":"int"}



# 第三方函数库
class Custom_function(Parser):
    '''自定义(第三方)函数(函数库) 处理器'''
    def __init__(self,*args,**kwargs) -> None:
        '''storage名称 nbt'''
        if len(args) >= 3:
            self.stack_frame,self.attribute_name,self.func_name = tuple(args[0:3])
    def main(self,func,*args,**kwargs) -> bool:
        # 系统 函数
        if(self.attribute_name == 'mc'):
            MCF =  mc_function()
            MCF.main(self.func_name,self.stack_frame[-1]["call_list"],func,**kwargs)
        # 自定义函数
        for item in custom_functions:
            if item['name'] == self.attribute_name:
                for item2 in item['functions']:
                    if item2['name'] == self.func_name:
                        self.write_file(func,f'#参数处理.赋值\n',**kwargs)
                        for i in range(len(item2['args'])):
                            if item2['args'][i]['type'] == 'storage':
                                self.write_file(func,f"data modify storage {item2['args'][i]['name']} set from storage {defualt_STORAGE} data.call_list[-1][{i}].value\n",**kwargs)
                        self.write_file(func,f'#自定义函数调用\n',**kwargs)
                        self.write_file(func,f"function {item2['call_path']}\n",**kwargs)
                        if item2['return']['type'] == 'storage':
                                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-2].return','append',{"value":0},func,**kwargs)
                                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-2].return[-1].value','set',f"storage {item2['return']['name']}",func,**kwargs)
                        return True
        #无
        return False

# 内置MC函数
class mc_function(Parser):
    '''内置MC函数'''
    def __init__(self,stack_frame):
        self.stack_frame = stack_frame
    def get_value(self,arg:ast,func=None,*args,**kwargs):
        if isinstance(arg,ast.Constant):
            return arg.value
        elif isinstance(arg,ast.Name):
            return self.py_get_value(arg.id,**kwargs)
        elif isinstance(arg,ast.List):
            var_list = []
            for item in arg.elts:
                var_list.append(self.get_value(item))
            return var_list
    def main(self,func_name,arg,func,*args,attribute_name=None,var=None,**kwargs):
        
        if attribute_name == None:
            ## mc 函数
            if(func_name == 'run'):
                command = self.get_value(arg[0],func,**kwargs) if len(arg) >= 1 else "say hello world"
                record = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else False
                flag = self.get_value(arg[2],func,**kwargs) if len(arg) >= 3 else "result"
                ##判断是否需要动态命令
                if not isinstance(arg[0],ast.List):
                    if record:
                        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].return','append',{"value":0},func,**kwargs)
                        self.write_file(func,f"execute store {flag} storage {defualt_STORAGE} stack_frame[-1].return[-1].value double 1.0 run {command}\n",**kwargs)
                    else:
                        self.write_file(func,f"{command}\n",**kwargs)
                else:
                    self.build_dynamic_command(arg[0].elts,func,**kwargs)

            if(func_name == 'MCEntity'):
                Entity = self.get_value(arg[0],func,**kwargs) if len(arg) >= 1 else "area_effect_cloud"
                Pos = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else "~ ~ ~"
                Nbt = self.get_value(arg[2],func,**kwargs) if len(arg) >= 3 else {}
                UUID = self.get_value(arg[3],func,**kwargs) if len(arg) >= 4 else get_uuid()
                if not Nbt.get("UUID"):
                    Nbt["UUID"] = str(uuid_to_list(UUID))
                Nbt = MCNbt(**Nbt)
                self.write_file(func,f"summon {Entity} {Pos} {Nbt}\n",**kwargs)
                Nbt = MCNbt(value = str(uuid_to_list(UUID)))
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].return','append',Nbt,func,**kwargs)
                return {"value":str(UUID),"type":mc.MCEntity}
            elif(func_name == 'example'):
                ...
            elif(func_name == 'NewFunction'):
                name = self.get_value(arg[0],func,**kwargs) if len(arg) >= 1 else "load"
                path = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else ""
                self.write_file(name,f"",p=path,f2=name,ClassName=kwargs.get("ClassName"))
                return {"value":True,"type":int}
            elif(func_name == 'WriteFunction'):
                name = self.get_value(arg[0],func,**kwargs) if len(arg) >= 1 else "load"
                Commands = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else []
                mode = self.get_value(arg[2],func,**kwargs) if len(arg) >= 3 else "a"
                path = self.get_value(arg[3],func,**kwargs) if len(arg) >= 4 else ""
                text = ''
                for item in Commands:
                    text += str(item)
                    text += '\n'
                self.write_file(name,text,p=path,f2=name,mode=mode,ClassName=kwargs.get("ClassName"))
                return {"value":True,"type":int}
            elif(func_name == 'newTags'):
                Tagsname = str(self.get_value(arg[0],func,**kwargs)) + '.json' if len(arg) >= 1 else "load.json"
                NameSpace = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else defualt_NAME
                Value = json.dumps({"replace": False,"values": self.get_value(arg[2],func,**kwargs)}, indent=2,ensure_ascii=False) if len(arg) >= 3 else json.dumps({"replace": False,"values": []}, indent=2,ensure_ascii=False)
                path = defualt_DataPath+NameSpace +'\\tags\\' + self.get_value(arg[3],func,**kwargs) if len(arg) >= 4 else defualt_DataPath+NameSpace +'\\tags\\'
                self.WriteT(Value,Tagsname,path)
                return {"value":True,"type":int}
            elif(func_name == 'checkBlock'):
                Pos = str(self.get_value(arg[0],func,**kwargs)) if len(arg) >= 1 else "0 0 0"
                Id = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else "air"
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].return','append',{"value":0},func,**kwargs)
                self.write_file(func,f"execute store success storage {defualt_STORAGE} stack_frame[-1].return[-1].value double 1.0 if block {Pos} {Id}\n",**kwargs)
                return {"value":1,"type":float}
            elif(func_name == 'rebuild'):
                ...
        else:
            ## mc 类处理
            if attribute_name == "MC.ENTITY":
                if(func_name == 'get_data'):
                    value = self.get_value(arg[0],func,**kwargs) if len(arg) >= 1 else "UUID"
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].return','append',{"value":0},func,**kwargs)
                    self.write_file(func,f"data modify storage {defualt_STORAGE} stack_frame[-1].return[-1].value set from entity {self.py_get_value(var)} {value}\n",**kwargs)

        return {"value":None,"type":None}


# 用户自定义类的调用
class ClassCall(Parser):
    '''自定义类 处理器'''
    def __init__(self,stack_frame,class_name=None,*args,**kwargs) -> None:
        self.stack_frame = stack_frame
        self.class_name = class_name
    def init(self,func,*args,**kwargs) -> bool:
        '''自定义类的实例化处理'''
        for item in self.stack_frame[0]["class_list"]:
            if item['id'] == self.class_name:
                self.write_file(func,f'#类方法调用.参数处理\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value set value []\n',**kwargs)
                for item2 in item['functions']:
                    if item2['id'] == "__init__":
                        shift = 0
                        for i in range(len(item2['args'])):
                            id = item2['args'][i]
                            if id != 'self':
                                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{id}"}}].value set from storage {defualt_STORAGE} data.call_list[-1][{i-shift}].value\n',**kwargs)
                            else:
                                shift +=1
                        self.write_file(func,f'#类方法调用.初始化\n',**kwargs)
                        self.write_file(func,f"function {defualt_NAME}:{item['id']}/{item2['id']}/_start\n",**kwargs)
                        break
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} stack_frame[-2].return[-1].value set from storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value\n',**kwargs)
                return {"value":[],"type":self.class_name}
        return {"value":None,"type":None}
    def main(self,var_name,class_name,call_name,IsCallFunc,func,storage,*args,**kwargs) -> list:
        # print(var_name,class_name,call_name,IsCallFunc)
        '''属性调用/方法调用
        var_name 变量名称 class_name 类名称 call_name 调用的名称 IsCallFunc 是否为调用函数
        '''
        if var_name == "self":
            class_name = kwargs["ClassName"]
        
        if IsCallFunc:
            for item in self.stack_frame[0]["class_list"]:
                if item['id'] == class_name:
                    for item2 in item['functions']:
                        if item2['id'] == call_name:
                            self.write_file(func,f'#参数处理.赋值\n',**kwargs)
                            ##判断参数是否含 self
                            IsHaveSelf = False
                            ##
                            #skip self 跳过self
                            shift = 0
                            for i in range(len(item2['args'])):
                                id = item2['args'][i]
                                if not id == "self":
                                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{id}"}}].value set from storage {defualt_STORAGE} data.call_list[-1][{i-shift}].value\n',**kwargs)
                                else:
                                    if var_name != None:
                                        # 如果有指定的 var_name
                                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value set from storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{var_name}"}}].value\n',**kwargs)
                                        # 如果没有则可能为方法调用方法
                                    else:
                                        if storage == None:
                                            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value set from storage {defualt_STORAGE} stack_frame[-1].return[-1].value\n',**kwargs)
                                        else:
                                            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value set from {storage}\n',**kwargs)
                                    shift += 1
                                    IsHaveSelf = True
                            self.write_file(func,f'\n#类方法调用\n',**kwargs)
                            
                            className =  item['id'] if item2['from'] == None else item2['from']
                            getprefix = self.get_func_info(className,item2['id'],**kwargs).get("prefix")
                            prefix = f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run "+getprefix if getprefix != None else f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run "
                            kwargs_ = copy.deepcopy(kwargs)
                            # if kwargs_.get("ClassName"):
                                # kwargs_.pop("ClassName")
                            self.mcf_call_function(f'{defualt_NAME}:{className}/{item2["id"]}/_start',func,isCustom=True,prefix=prefix,**kwargs_)
                            if IsHaveSelf:
                                ## 重新修改变量的值
                                if var_name != None:
                                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{var_name}"}}].value set from storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value\n',**kwargs)
                                elif storage != None:
                                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage} set from storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value\n',**kwargs)
                            selfVar = "" # self变量对应的变量
                            if var_name != None:
                                selfVar = f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{var_name}"}}].value'
                            elif storage != None:
                                selfVar = f'{storage}'
                            else:
                                selfVar = f'storage {defualt_STORAGE} stack_frame[-1].return[-1].value'
                            return {"value":[],"type":item2['type'],"selfVar":selfVar,"success":True}
        else:
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} stack_frame[-2].return[-1].value set from storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{var_name}"}}][{{"id":"{call_name}"}}].value\n',**kwargs)
        #无
        return {"value":None,"type":None}

    def class_var_to_str(self,tree:ast.Attribute,func,**kwargs):
        '''将实例化对象调用的值转 字符串
        
        - 主要用于 赋值中的类处理
        - 例如：

        >>> self.a.x = 1
        '''
        if isinstance(tree.value,ast.Attribute):
            return self.class_var_to_str(tree.value,func,**kwargs) + f'[{{"id":"{tree.attr}"}}].value'
        elif isinstance(tree.value,ast.Name):
            return f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{tree.value.id}"}}].value[{{"id":"{tree.attr}"}}].value'
            # return f'[{{"id":"{tree.attr}"}}].value'
        return ""

    def modify_class_var(self,tree:ast.Attribute,func,value,**kwargs):
        '''python 修改 类的嵌套属性
        - 例如：

        >>> self.a.x = 3
        '''
        temp = self.get_class_var(tree,func,**kwargs)
        if isinstance(value,str):
            value = "\""+str(value)+"\""
        temp["value"] = value
        temp["type"] = self.check_type(value)
        StoragePath = self.class_var_to_str(tree,func,**kwargs)
        
        self.mcf_modify_value_by_value(f'{StoragePath[0:-5]}type','set',self.check_type(value),func,**kwargs)


    def get_class_var(self,tree:ast.Attribute,func,**kwargs):
        '''python 获取 类的嵌套属性
        - 例如：

        >>> self.a.x
        '''
        if isinstance(tree.value,ast.Attribute):
            x = self.get_class_var(tree.value,func,**kwargs)
            for j in x["value"]:
                if j.get("id") == tree.attr:
                    return j
            x["value"].append({"id":tree.attr,"value":[],"type":None})
            return x["value"][-1]

        elif isinstance(tree.value,ast.Name):
            for i in self.stack_frame[-1]['data']:
                if i.get('id') == tree.value.id:
                    for j in i['value']:
                        if j.get('id') == tree.attr:
                            return j
                    i['value'].append({"id":tree.attr,"value":[]})
                    return i['value'][-1]
            self.stack_frame[-1]['data'].append({"id":tree.value.id,"value":[{"id":tree.attr,"value":[],"type":None}],"type":None})
            return self.stack_frame[-1]['data'][-1]['value'][-1]



# 类型的属性调用 + py内置方法与属性
class TypeAttributeHandler(Parser):
    '''根据类型处理 属性'''
    def __init__(self,tree,value ,Type,attr:str,name:str,IsCallFunc:int, *args, **kwargs):
        self.stack_frame = tree
        self.Value = value
        self.type = Type
        self.name = name
        self.IsCallFunc = IsCallFunc
        self.attr = attr
        self.storage = kwargs.get("storage")
        if self.storage == None:
            self.storage = f'storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{self.name}"}}].value'
    def get_value(self,arg,func=None,*args,**kwargs):
        if isinstance(arg,ast.Constant):
            return arg.value
        elif isinstance(arg,ast.Name):
            return self.py_get_value(arg.id,**kwargs)
        elif isinstance(arg,ast.List):
            var_list = []
            for item in arg.elts:
                var_list.append(self.get_value(item))
            return var_list
    def main(self,func,IsInbuilt=False,**kwargs):
        # 类型:
        #       变量,
        #       函数
        
        # 系统内置类
        if self.type == "str":
            if not self.IsCallFunc:
                if self.attr == "__hash__":
                    return {"value":self.Value.__hash__()%2147483647,"type":"int"}
            else:
                if self.attr == "replace":
                    return {"value":self.Value.replace(self.get_value(self.stack_frame[-1]["call_list"][0]),self.get_value(self.stack_frame[-1]["call_list"][1])),
                    "type":"str"}
        if self.type == "list":
            if not self.IsCallFunc:
                
                if self.attr == "hash":
                    return {"value":self.Value.__hash__()%2147483647,"type":"int"}
            else:
                if self.attr == "append":
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {self.storage} append from storage {defualt_STORAGE} data.call_list[-1][-1].value\n',**kwargs)
                    return {"value":self.Value.append(self.get_value(self.stack_frame[-1]["call_list"][0])),"type":"list"}
                elif self.attr == "pop":
                    #动态命令
                    self.mcf_build_dynamic_command([f'storage {defualt_STORAGE} data.call_list[-1][-1].value'],[f'$data remove {self.storage}[$(arg0)]'],func,**kwargs)
                    index = self.get_value(self.stack_frame[-1]["call_list"][0])
                    if not isinstance(index,int):
                        index = 0
                        if self.Value:
                            return {"value":self.Value.pop(0),"type":"list"}
                    try:
                        return {"value":self.Value.pop(index),"type":"list"}
                    except:
                        if self.Value:
                            return {"value":self.Value.pop(0),"type":"list"}
                        return {"value":self.Value,"type":"list"}
        # 自定义的类
        elif not IsInbuilt:
            # if not self.IsCallFunc:
            
            ClassC = ClassCall(self.stack_frame,self.type,**kwargs)
            x:dict=ClassC.main(self.name,self.type,self.attr,self.IsCallFunc,func,self.storage,**kwargs)
            
            if self.IsCallFunc and x.get('success'): #是否成功调用自定义类的方法
                x["haveCallFunc"] = True
            return x
            # else:
            #     self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} stack_frame[-2].return[-1].value set from storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{self.name}"}}][{{"id":"{self.attr}"}}].value\n',**kwargs)
            #     return [None,None]
        
        return {"value":None,"type":None}

# 装饰器处理器
class DecoratoHandler(Parser):
    def __init__(self,stack_frame):
        self.stack_frame = stack_frame
    def check(self,decorator):
        '''条件判断'''
        if (isinstance(decorator,ast.Call) and 
            isinstance(decorator.func,ast.Attribute) and 
            isinstance(decorator.func.value,ast.Attribute) and 
            isinstance(decorator.func.value.value,ast.Name) and 
            decorator.func.value.value.id == "mc" and 
            decorator.func.value.attr == 'event'): return 1
        elif (isinstance(decorator,ast.Attribute) and
            isinstance(decorator.value,ast.Attribute) and
            isinstance(decorator.value.value,ast.Name) and 
            decorator.value.value.id == 'mc' and
            decorator.value.attr == 'event'): return 2
        elif (isinstance(decorator,ast.Call) and 
            isinstance(decorator.func,ast.Attribute) and 
            isinstance(decorator.func.value,ast.Attribute) and 
            isinstance(decorator.func.value.value,ast.Name) and 
            decorator.func.value.value.id == "mc" and 
            decorator.func.value.attr == 'exec'): return 3
        elif (isinstance(decorator,ast.Attribute) and 
            isinstance(decorator.value,ast.Name) and
            decorator.value.id == "mc" and 
            decorator.attr == 'cache'): return 4
        elif (isinstance(decorator,ast.Call) and 
            isinstance(decorator.func,ast.Attribute) and 
            isinstance(decorator.func.value,ast.Name) and
            decorator.func.value.id == "mc" and 
            decorator.func.attr == 'tag'): return 5
        return None

    def main(self,decorator,callFunctionName,*args, **kwargs):
        if self.check(decorator) == 1 or self.check(decorator) == 2:
            events = EventHandler()
            events.main(decorator,self.stack_frame[0]["eventCounter"],callFunctionName,**kwargs)
        if self.check(decorator) == 3:
            events = ExecHandler(self.stack_frame)
            self.stack_frame = events.main(decorator,callFunctionName,**kwargs)
        if self.check(decorator) == 4:
            events = CacheHandler(self.stack_frame)
            self.stack_frame = events.main(decorator,callFunctionName,**kwargs)
        if self.check(decorator) == 5:
            events = FunctionTagHandler(self.stack_frame)
            self.stack_frame = events.main(decorator,callFunctionName,**kwargs)
        return self.stack_frame

# 监听事件处理器
class EventHandler(DecoratoHandler):
    def __init__(self):
        ...
    def main(self,decorator,eventCounter,callFunctionName,*args, **kwargs):
        if self.check(decorator) == 1:
            if(decorator.func.attr == 'ifEntytPosDownZero'):
                # call
                self.write_file(f"",f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run function {defualt_NAME}:events/event_{eventCounter}/_start",f2='tick')
                self.write_file(
                    f"events//event_{eventCounter}",
                    f"#检测\nscoreboard players set #{defualt_NAME}.sys.events_{eventCounter}.pass {scoreboard_objective} 0\nfunction {defualt_NAME}:events/event_{eventCounter}/check\n#通过\nexecute if score #{defualt_NAME}.sys.events_{eventCounter}.pass {scoreboard_objective} matches 1 run function {defualt_NAME}:{callFunctionName}/_start",
                    f2='_start')
                # check
                
                self.mcf_new_predicate('{"condition": "location_check","predicate": {"position": {"y": {"max": -0.00000000000000001}}}}',"is_down_zero")

                Selector = '@s'
                for i in decorator.args:
                    if isinstance(i,ast.Constant):
                        Selector = i.value

                self.write_file(f"events//event_{eventCounter}",f"execute as {Selector} at @s if predicate {defualt_NAME}:is_down_zero run scoreboard players set #{defualt_NAME}.sys.events_{eventCounter}.pass {scoreboard_objective} 1",f2='check')
        elif self.check(decorator) == 2:
            if(decorator.attr == 'entityDeath'):
                ...

# exec处理器
class ExecHandler(DecoratoHandler):
    def __init__(self,stack_frame):
        self.stack_frame = stack_frame
    def main(self,decorator,callFunctionName,*args, **kwargs):
        if self.check(decorator) == 3:
            if(decorator.func.attr == 'AS') or (decorator.func.attr == 'AT'):
                # call
                prefix = f"execute "
                Selector = '' if decorator.args else f'{decorator.func.attr.lower()} @s '
                for i in decorator.args:
                    if isinstance(i,ast.Constant):
                        Selector += f'{decorator.func.attr.lower()} {i.value} '
                prefix += f"{Selector}run "
                x = self.get_func_info(kwargs.get("ClassName") if kwargs.get("ClassName") else "",callFunctionName,**kwargs)
                
                if x.get("prefix"):
                    x['prefix'] += prefix
                else:
                    x['prefix'] = prefix
        return self.stack_frame

# 函数标签处理器
class FunctionTagHandler(DecoratoHandler):
    def __init__(self,stack_frame):
        self.stack_frame = stack_frame
    def main(self,decorator,callFunctionName,*args, **kwargs):
        if self.check(decorator) == 5:
            if(decorator.func.attr == 'tag') or (decorator.func.attr == 'AT'):
                # call
                if decorator.args:
                    Tagsname = decorator.args[0].value + '.json'
                    NameSpace = decorator.args[1].value if len(decorator.args) >= 2 else "minecraft"
                    functionName = self.get_func_info(kwargs.get("ClassName"),callFunctionName,**kwargs).get("callPath").replace('_start','_call')
                    path = defualt_DataPath+NameSpace +'\\tags\\functions\\'
                    self.mcf_func_tags_add(path,Tagsname,functionName)
                    kwargs['f2'] = f'_call'
                    self.mcf_new_stack(callFunctionName,**kwargs)
                    self.write_file(callFunctionName,f'#函数调用\n',**kwargs)
                    self.write_file(callFunctionName,f'function {self.get_func_info(kwargs.get("ClassName"),callFunctionName,**kwargs).get("callPath")}\n',**kwargs)
                    self.mcf_remove_stack_data(callFunctionName,**kwargs)
                    self.write_file(callFunctionName,f'##  调用结束\n',**kwargs)
        return self.stack_frame

# 函数缓存处理器
class CacheHandler(DecoratoHandler):
    def __init__(self,stack_frame):
        self.stack_frame = stack_frame
    def main(self,decorator,callFunctionName,*args, **kwargs):
        x = self.get_func_info(kwargs.get("ClassName") if kwargs.get("ClassName") else "",callFunctionName,**kwargs)
        x['cached'] = True
        self.write_file(callFunctionName,f"##缓存函数-判断缓存数据\n    #先字符串化参数\n",**kwargs)
        # 参数转字符串
            #动态命令
        # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].dync','set',{},callFunctionName,**kwargs)
        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} stack_frame[-1].dync.arg0','set',f'storage {defualt_STORAGE} data.call_list[-1]',callFunctionName,**kwargs)
        self.mcf_call_function(f'{callFunctionName}/dync_{self.stack_frame[0]["dync"]}/_start with storage {defualt_STORAGE} stack_frame[-1].dync',callFunctionName,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        
        self.write_file(callFunctionName,f"    #字符串的参数作为键，索引结果\n",**kwargs)
        self.write_file(callFunctionName,f"execute if score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run return 1\n",**kwargs)
        self.mcf_call_function(f'{callFunctionName}/dync_{self.stack_frame[0]["dync"]+1}/_start with storage {defualt_STORAGE} stack_frame[-1].dync',callFunctionName,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        # 内容
        kwargs['p'] = f'{callFunctionName}//dync_{self.stack_frame[0]["dync"]}//'
        kwargs['f2'] = f'_start'

        self.write_file(callFunctionName,f'##    动态命令\n$data modify storage {defualt_STORAGE} stack_frame[-1].dync.arg0 set value \'$(arg0)\'\n$data modify storage {defualt_STORAGE} stack_frame[-1].key set value \'$(arg0)\'\n',inNewFile=True,**kwargs)
        self.stack_frame[0]["dync"] += 1
        # 字符串的参数作为键，索引结果
        # 内容
        kwargs['p'] = f'{callFunctionName}//dync_{self.stack_frame[0]["dync"]}//'
        CachedData = f'storage {defualt_STORAGE} stack_frame[0].CachedFunctions[{{"id":"{callFunctionName}"}}].\'$(arg0)\''
        if kwargs.get("ClassName"):
            CachedData = f'storage {defualt_STORAGE} stack_frame[0].CachedMethod[{{"id":"{kwargs.get("ClassName")}"}}].value[{{"id":"{callFunctionName}"}}].\'$(arg0)\''
        self.write_file(callFunctionName,f'##    动态命令\n$execute if data {CachedData} run scoreboard players set #{defualt_STORAGE}.stack.end {scoreboard_objective} 1\n$execute if data {CachedData} run data modify storage {defualt_STORAGE} stack_frame[-2].return append from {CachedData}\n',inNewFile=True,**kwargs)
        self.stack_frame[0]["dync"] += 1


        # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} stack_frame[-1].dync','set',{},callFunctionName,**kwargs)
        return self.stack_frame

# 魔术方法处理器
class MagicMethodHandler(ClassCall):
    def __init__(self,stack_frame,*args,**kwargs) -> None:
        self.stack_frame = stack_frame
    
    def addArgs(self,inputArgs,func,*args,**kwargs):
        '''参数添加'''
        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list','append',[],func,**kwargs)
        for i in inputArgs:
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.call_list[-1]','append',i,func,**kwargs)


    def main(self,var_name,class_name,call_name,func,inputArgs=None,storage=None,*args,**kwargs) -> list:
        # print(var_name,class_name,call_name,IsCallFunc)
        '''属性调用/方法调用
        var_name 变量名称 class_name 类名称 call_name 调用的方法名称 IsCallFunc 是否为调用函数\ninputArgs 传入的参数集（不包括self)
        '''
        if var_name == "self":
            class_name = kwargs["ClassName"]  
        
        for item in self.stack_frame[0]["class_list"]:
            if item['id'] == class_name:
                for item2 in item['functions']:
                    if item2['id'] == call_name:
                        # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} data.call_list','append',[],func,**kwargs)
                        self.addArgs(inputArgs,func,*args,**kwargs)
                        self.mcf_new_stack(func,**kwargs)
                        # self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} data.call_list','set',f'storage {defualt_STORAGE} data.call_list',func,**kwargs)
                        self.write_file(func,f'#魔术方法-参数处理.赋值\n',**kwargs)
                        
                        ##判断参数是否含 self
                        IsHaveSelf = False
                        ##
                        #skip self 跳过self
                        shift = 0
                        for i in range(len(item2['args'])):
                            id = item2['args'][i]
                            if not id == "self":
                                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"{id}"}}].value set from storage {defualt_STORAGE} data.call_list[-1][{i-shift}].value\n',**kwargs)
                            else:
                                # 遇到 self变量
                                if var_name != None:
                                    # 如果有指定的 var_name
                                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value set from storage {defualt_STORAGE} stack_frame[-2].data[{{"id":"{var_name}"}}].value\n',**kwargs)
                                # 如果没有则可能为方法调用方法，可能为链性函数
                                else:
                                    if storage == None:
                                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value set from storage {defualt_STORAGE} stack_frame[-2].return[-1].value\n',**kwargs)
                                    else:
                                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value set from {storage}\n',**kwargs)
                                shift += 1
                                IsHaveSelf = True
                        
                        self.write_file(func,f'\n#魔术方法-调用\n',**kwargs)
                        
                        className =  item['id'] if item2['from'] == None else item2['from']
                        getprefix = self.get_func_info(className,item2['id'],**kwargs).get("prefix")
                        prefix = f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run "+getprefix if getprefix != None else f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run "
                        kwargs_ = copy.deepcopy(kwargs)
                        # if kwargs_.get("ClassName"):
                            # kwargs_.pop("ClassName")
                        self.mcf_call_function(f'{defualt_NAME}:{className}/{item2["id"]}/_start',func,isCustom=True,prefix=prefix,**kwargs_)
                        if IsHaveSelf:
                            ## 重新修改变量self的值
                            if var_name != None:
                                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} stack_frame[-2].data[{{"id":"{var_name}"}}].value set from storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value\n',**kwargs)
                            elif storage != None:
                                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage} set from storage {defualt_STORAGE} stack_frame[-1].data[{{"id":"self"}}].value\n',**kwargs)
                        self.mcf_remove_stack_data(func,**kwargs)
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} data.call_list[-1]\n',**kwargs)
                        return {"value":[],"type":item2['type']}
