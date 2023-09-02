import ast
import copy
import json
import os
import re

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
        self.main_tree:list[dict] = []
        self.py_append_tree()
        #初始化计分板
        self.write_file('',f'scoreboard objectives add {scoreboard_objective} dummy\n',f2="_init",**kwargs)
        # self.write_file('',f'scoreboard objectives remove {scoreboard_objective2} dummy\n',f2="_init",**kwargs)
        self.write_file('',f'scoreboard objectives add {scoreboard_objective2} dummy\n',f2="_init",**kwargs)
        self.write_file('__main__',f'scoreboard players reset * {scoreboard_objective2}\n',**kwargs)
        self.write_file('__main__',f'#初始化栈\n',**kwargs)
        self.write_file('__main__',f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree set value [{{"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{{}}}}]\n',**kwargs)
        self.parse('__main__',**kwargs)
    def parse(self,func:str,*args,**kwargs):
        '''func为当前函数的名称'''
        code = copy.deepcopy(self.code)
        code_ = ast.parse(code)
        #遍历python的ast树
        self.walk(code_.body,func,-1,**kwargs)
        print(self.main_tree)
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
                self.main_tree[-1]['Is_code_have_end'] = True
                self.Return(item,func,**kwargs)
            # 逻辑运算
            elif isinstance(item,ast.If):
                self.main_tree[-1]['condition_time'] = 0
                self.main_tree[-1]['elif_time'] = 0
                self.main_tree[-1]['BoolOpTime'] += 1
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.end {scoreboard_objective} 0\n',**kwargs)
                self.If(item,self.main_tree[-1]['condition_time'],func,True,**kwargs)
            # while 循环
            elif isinstance(item,ast.While):
                self.main_tree[-1]["In_loop"] = True
                self.main_tree[-1]['BoolOpTime'] += 1
                self.While(item,func,**kwargs)
                self.main_tree[-1]["In_loop"] = False
            # For 循环 
            elif isinstance(item,ast.For):
                self.main_tree[-1]["In_loop"] = True
                self.main_tree[-1]['BoolOpTime'] += 1
                self.For(item,func,**kwargs)
                self.main_tree[-1]["In_loop"] = False
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

        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','append',[],func,**kwargs)

        for i in range(len(commands)):
            self.Expr_set_value(ast.Assign(targets=[ast.Name(id=None)],value=commands[i]),func,**kwargs)
        # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].dync','set',{},func,**kwargs)
        for i in range(len(commands)):
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].dync.arg{i}','set',f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][{i}].value',func,**kwargs)
        self.mcf_call_function(f'{func}/dync_{self.main_tree[0]["dync"]}/_start with storage {defualt_STORAGE} main_tree[-1].dync',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].dync','set',{},func,**kwargs)
        self.write_file(func,f'data remove storage {defualt_STORAGE} main_tree[-1].call_list[-1]\n',**kwargs)
        # 内容
        kwargs['p'] = f'{func}//dync_{self.main_tree[0]["dync"]}//'
        kwargs['f2'] = f'_start'
        self.write_file(func,f'##    动态命令\n$',inNewFile=True,**kwargs)
        for i in range(len(commands)):
            self.write_file(func,f'$(arg{i})',inNewFile=True,**kwargs)
        self.main_tree[0]["dync"] += 1
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
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].dync.arg{i}','set',inputArgs[i],func,**kwargs)
        self.mcf_call_function(f'{func}/dync_{self.main_tree[0]["dync"]}/_start with storage {defualt_STORAGE} main_tree[-1].dync',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        self.write_file(func,f'    ##动态命令调用end\n',**kwargs)
        # 内容
        kwargs['p'] = f'{func}//dync_{self.main_tree[0]["dync"]}//'
        kwargs['f2'] = f'_start'

        self.write_file(func,f'##    动态命令\n',inNewFile=True,**kwargs)
        # 
        for i in runFunction:
            self.write_file(func,i+'\n',inNewFile=True,**kwargs)
        self.main_tree[0]["dync"] += 1
##

## 赋值
# 赋值
    def Assign(self,tree:ast.Assign,func:str,index:-1,*args,**kwargs):
        '''赋值操作'''
        # 类型扩建TODO
        if isinstance(tree.value,ast.BinOp):
            tree.value = self.BinOp(tree.value,tree.value.op,func,index,index,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,tree.value.value,False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,tree.value.value,index,True,True,func,**kwargs)
                    if (tree.value.kind == None):
                        self.mcf_add_exp_operation(tree.value.value,func,index)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value\n',**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value',func,**kwargs)
                    ClassC.modify_class_var(i,func,tree.value)
            self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,tree.value.value,True,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,tree.value.value,index,True,True,func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_value(f'{StoragePath}','set',tree.value.value,func,**kwargs)
                    ClassC.modify_class_var(i,func,tree.value.value,**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value2(i.id,tree.value.id,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,self.py_get_type(tree.value.id,index),index,False,True,func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{tree.value.id}"}}].value',func,**kwargs)
                    ClassC.modify_class_var(i,func,self.py_get_value(tree.value.id,func,**kwargs))
        elif isinstance(tree.value,ast.Subscript):
            # 切片赋值
            value = 0
            value = self.Subscript(tree.value,func,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,None,index,True,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    if(is_global):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value\n',**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value\n',**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value',func,**kwargs)
                    ClassC.modify_class_var(i,func,value,**kwargs)
        elif isinstance(tree.value,ast.Call):
            # 函数返回值 赋值
            value = self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # python 赋值 主要是查是否为全局变量
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value[0],False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,value[1],index,False,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
                    ClassC.modify_class_var(i,func,value,**kwargs)
        elif isinstance(tree.value,ast.Attribute):
            # 函数返回值 赋值
            value = self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # python 赋值 主要是查是否为全局变量
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value[0],False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,value[1],index,True,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
                    x = ClassC.get_class_var(tree.value,func,**kwargs)
                    ClassC.modify_class_var(i,func,x["value"],**kwargs)
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
                        self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                    self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_change_value_by_scoreboard(f'{StoragePath[8:]}',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                    ClassC.modify_class_var(i,func,1,**kwargs)
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
                        self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_store_value_by_run_command(StoragePath,f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    ClassC.modify_class_var(i,func,1,**kwargs)
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
                        self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_store_value_by_run_command(StoragePath,f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    ClassC.modify_class_var(i,func,1,**kwargs)
            self.mcf_old_stack_cover_data(func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.List):
            self.List(tree.value,func,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,self.main_tree[-1]["list_handler"],False,func,False,index,**kwargs)
                    self.py_change_value_type(i.id,[],index,True,True,func,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    if(is_global):
                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[-1].list_handler\n',**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[-1].list_handler\n',**kwargs)
                elif isinstance(i,ast.Attribute):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(i,func,**kwargs)
                    self.mcf_modify_value_by_from(f'{StoragePath}','set',f'storage {defualt_STORAGE} main_tree[-1].list_handler',func,**kwargs)
                    ClassC.modify_class_var(i,func,self.main_tree[-1]["list_handler"],**kwargs)
# 类型注解赋值
    def AnnAssign(self,tree:ast.AnnAssign,func:str,index:-1,*args,**kwargs):
        '''带有类型注释的赋值'''
        # tree.annotation
        self.Assign(ast.Assign(targets=[tree.target],value=tree.value),func,index)
        self.py_change_value_type(tree.target.id,tree.annotation.id,-1,False,True,func)
# 增强分配
    def AugAssign(self,tree:ast.AugAssign,func:str,index:-1,*args,**kwargs):
        '''变量 赋值操作 += -= /= *='''
        # 类型扩建TODO
        if isinstance(tree.value,ast.BinOp):
            tree.value = self.BinOp(tree.value,tree.value.op,func,index,index,**kwargs)
            i =  tree.target
            if isinstance(i,ast.Name):
                value = self.get_operation(self.py_get_value(i.id,func,index),tree.value.value,tree.op,func)
                self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                if (tree.value.kind == None):
                    self.mcf_add_exp_operation(tree.value.value,func,index)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[{index}].exp_operation insert -1 from storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{i.id}"}}].value\n',**kwargs)
                self.mcf_change_exp_operation(tree.op,func,self.py_get_type(i.id,func,index),self.check_type(tree.value.value),index)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value\n',**kwargs)
            self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            i =tree.target
            if isinstance(i,ast.Name):
                value = tree.value.value
                self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[{index}].temp set value {value}\n',**kwargs)
                self.mcf_change_value_by_operation(i.id,value,self.py_get_value_global(i.id,func,-1),tree.op,func,index,f'storage {defualt_STORAGE} main_tree[{index}].temp',**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            i = tree.target
            if isinstance(i,ast.Name):
                value = self.get_operation(self.py_get_value(i.id,func,index),self.py_get_value(tree.value.id,func,index),tree.op,func,**kwargs)
                self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                self.mcf_change_value_by_operation(i.id,tree.value.id,self.py_get_value_global(i.id,func,-1),tree.op,func,index,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            # 切片赋值
            self.Subscript(tree.value,func,**kwargs)
            value = 0
            i =tree.target
            if isinstance(i,ast.Name):
                self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                is_global = self.py_get_value_global(i.id,func,index,**kwargs)
            # mcf 赋值
                self.mcf_change_value_by_operation2(f'{defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value',f'{defualt_STORAGE} main_tree[-1].Subscript[-1].value',tree.op,func,-1,**kwargs)
                if(is_global):
                    self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value',f'#{defualt_NAME}.sys.temp1 {scoreboard_objective}','double',0.001,func,**kwargs)
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
                self.mcf_change_value_by_operation2(f'{defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value',f'{defualt_STORAGE} main_tree[-1].return[-1].value',tree.op,func,-1,**kwargs)
                if(is_global):
                    self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value',f'#{defualt_NAME}.sys.temp1 {scoreboard_objective}','double',0.001,func,**kwargs)
## Global
    def Global(self,tree:ast.Global,func:str,index:-1,*args,**kwargs):
        '''Global 全局变量 '''
        for i in tree.names:
            for j in self.main_tree[0]["data"]:
                if j["id"] == i:
                    self.main_tree[index]["data"].append({"id":i,"value":j["value"],"is_global":True})
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{j["id"]}"}}].value set from storage {defualt_STORAGE} main_tree[0].data[{{"id":{j["id"]}}}].value\n',**kwargs)

# 运算
    def BinOp(self,tree:ast.BinOp,op:ast.operator,func:str,index:-1,index2:-1,time=0,*args,**kwargs) -> ast.Constant:
        '''运算操作
        tree新的树，op操作类型 +-*/
        time 处理常量运算
        调用完后，并且处理完返回值，需 移除计算数据
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
                # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree_list[item].id}"}}]',func,**kwargs)
                tree_list[item] = ast.Constant(value=value, kind=["is_v",self.py_get_type(tree_list[item].id,index)])
            # 假如为函数返回值
            elif isinstance(tree_list[item],ast.Call):
                # 函数返回值 赋值
                value = self.Expr(ast.Expr(value=tree_list[item]),func,-1,*args,**kwargs)
                # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',f'storage {defualt_STORAGE} main_tree[-1].return[-1]',func,**kwargs)
                tree_list[item] = ast.Constant(value=value[0], kind=["is_call",value[1]])
            elif isinstance(tree_list[item],ast.Subscript):
                # 切片赋值
                self.Subscript(tree_list[item],func,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value',func,**kwargs)
                value = 0
                tree_list[item] = ast.Constant(value=value, kind=["is_call",None])
            elif isinstance(tree_list[item],ast.Attribute):
                # 函数返回值 赋值
                value = self.Expr(ast.Expr(value=tree_list[item]),func,-1,**kwargs)
                # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',f'storage {defualt_STORAGE} main_tree[-1].return[-1]',func,**kwargs)
                tree_list[item] = ast.Constant(value=value[0], kind=["is_v",value[1]])
        tree.left,tree.right = (tree_list[0],tree_list[1])
        # 常量处理
        if isinstance(tree.left,ast.Constant) and isinstance(tree.right,ast.Constant):
            ## mcf 处理
            if (tree.left.kind == None) and (tree.right.kind == None ):
                #常量
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                if not time:
                    self.mcf_add_exp_operation(value,func,index,**kwargs)
                return ast.Constant(value=value, kind=["have_operation",self.check_type(value)])
            # have_operation标记没有涉及到变量的 常量之间的运算
            elif (tree.left.kind != None and tree.left.kind[0] == "have_operation" and tree.left.kind[1] != None) and (tree.right.kind != None and tree.right.kind[0] == "have_operation" and tree.right.kind[1] != None):
                # 涉及到 已经运算过的式子的之间的运算（）
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                if not time:
                    self.mcf_add_exp_operation(value,func,index,**kwargs)
                return ast.Constant(value=value, kind=["have_operation",self.check_type(value)])
            elif (tree.left.kind != None and tree.left.kind[0] == "have_operation" and tree.left.kind[1] != None) and (tree.right.kind == None):
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                if not time:
                    self.mcf_add_exp_operation(value,func,index,**kwargs)
                return ast.Constant(value=value, kind=["have_operation",self.check_type(value)])
            elif (tree.left.kind == None) and (tree.right.kind != None and tree.right.kind[0] == "have_operation" and tree.right.kind[1] != None):
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                if not time:
                    self.mcf_add_exp_operation(value,func,index,**kwargs)
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
            self.main_tree[0]["functions"].append({"id":func,"args":[],"call":"_start","type":Return_type,"callPath":callpath})
        #读取函数参数
        args_list = []
        for item in tree.args.args:
            if isinstance(item,ast.arg):
                if not kwargs.get("ClassName"):
                    self.main_tree[0]["functions"][-1]["args"].append(item.arg)
                args_list.append(item.arg)
        if kwargs.get("ClassName"):
            callpath = defualt_NAME+":"+kwargs.get("ClassName")+"/"+func+"/_start"
            self.py_get_class_add_function(kwargs.get("ClassName"),[func,Return_type,args_list,None,callpath])
        #装饰器处理器
        if tree.decorator_list:
            for i in tree.decorator_list:
                DH = DecoratoHandler(self.main_tree)
                self.main_tree = DH.main(i,func,**kwargs)
        #
        if kwargs.get("f2"):
            kwargs.pop("f2")
        f2 = "_start"
        if self.get_func_info(kwargs.get("ClassName"),func,**kwargs).get("cached"):
            f2 = "_start2"
        

        #函数参数初始化
        self.write_file(func,f'##函数参数初始化\n',f2=f2,**kwargs)
        self.FunctionDef_args_init(tree.args,args_list,func,index,f2=f2,**kwargs)
        
        #

        
        self.write_file(func,f'##函数主体\n',f2=f2,**kwargs)
        
        self.walk(tree.body,func,index,f2=f2,**kwargs)
        # 如果无返回，则返回字符串None
        if not self.main_tree[-1]['Is_code_have_end']:
            self.Return(ast.Return(value=ast.Constant(value="None", kind=None)),func,f2=f2,**kwargs)
        self.write_file(func,f'##函数结尾\n',f2=f2,**kwargs)
        if f2 == "_start2":
            funcName = f'{func}/_start2'
            self.mcf_call_function(funcName,func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1.. run ',**kwargs)
        # 若该函数为缓存函数，则存储返回结果
        if f2 == "_start2":
            # 内容
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].dync.arg0','set',f'storage {defualt_STORAGE} main_tree[-1].key',func,**kwargs)
            self.mcf_call_function(f'{func}/dync_{self.main_tree[0]["dync"]}/_start with storage {defualt_STORAGE} main_tree[-1].dync',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1.. run ',**kwargs)
            kwargs['p'] = f'{func}//dync_{self.main_tree[0]["dync"]}//'
            CachedData = f'storage {defualt_STORAGE} main_tree[0].CachedFunctions[{{"id":"{func}"}}].value.\'$(arg0)\''
            if kwargs.get("ClassName"):
                CachedData = f'storage {defualt_STORAGE} main_tree[0].CachedMethod[{{"id":"{kwargs.get("ClassName")}"}}].value[{{"id":"{func}"}}].value.\'$(arg0)\''
            if not self.main_tree[-1]['Is_code_have_end']:
                self.write_file(func,f'##    动态命令\n$data modify {CachedData} set value {{"value":"None"}}\n',inNewFile=True,**kwargs)
            else:
                self.write_file(func,f'##    动态命令\n$data modify {CachedData} set from storage {defualt_STORAGE} main_tree[-2].return[-1]\n',inNewFile=True,**kwargs)
            # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].dync','set',{},func,**kwargs)
            
            self.main_tree[0]["dync"] += 1
        self.main_tree.pop(-1)
# 函数参数处理 参数预先值
    def FunctionDef_args_init(self,tree:ast.arguments,args_list:list,func:str,index:-1,*args,**kwargs):
        '''函数定义中 参数预先值'''
        # 类型扩建TODO
        for i in range(-1,-1*len(tree.defaults)-1,-1):
            if isinstance(tree.defaults[i],ast.BinOp):
                value = self.BinOp(tree.defaults[i],tree.defaults[i].op,func,index,index-1,**kwargs)
                self.py_change_value(args_list[i],value.value,False,func,False,index,**kwargs)
                if (value.kind == None):
                    self.mcf_add_exp_operation(value.value,func,index)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute unless data storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{args_list[i]}"}}] run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{args_list[i]}"}}].value set from storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value\n',**kwargs)
                self.mcf_remove_Last_exp_operation(func,**kwargs)
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
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','append',[],func,**kwargs)
                self.main_tree[-1]["call_list"] = []
                #位置传参
                for i in range(len(Call.args)):
                    self.Expr_set_value(ast.Assign(targets=[ast.Name(id=None)],value=Call.args[i]),func,**kwargs)
                #关键字传参
                for i in range(len(Call.keywords)):
                    if isinstance(Call.keywords[i],ast.keyword):
                        self.Expr_set_value(ast.Assign(targets=[ast.Name(id=Call.keywords[i].arg)],value=Call.keywords[i].value),func,**kwargs)
                self.mcf_new_stack(func,**kwargs)

                if(len(Call.args)!=0 or len(Call.keywords) != 0):
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list','set',f'storage {defualt_STORAGE} main_tree[-2].call_list',func,**kwargs)
                ## 优先判断该函数是否已存在，若未存在，即可能为类实例化
                if self.check_function_exist(func_name,**kwargs):
                    ## mcf
                    self.write_file(func,f'#参数处理.赋值\n',**kwargs)
                    #位置传参
                    for i in range(len(args)):
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{args[i]}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][{i}].value',func,**kwargs)
                    #关键字传参
                    for i in range(len(Call.keywords)):
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{Call.keywords[i].arg}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][{{"id":{Call.keywords[i].arg}}}].value',func,**kwargs)
                    self.write_file(func,f'#函数调用\n',**kwargs)
                    getprefix = self.get_func_info("",func_name,**kwargs).get("prefix")
                    prefix = f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run "+getprefix if getprefix != None else f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run "
                    self.mcf_call_function(f'{func_name}/{call_name}',func,prefix=prefix,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
                    self.write_file(func,f'##  调用结束\n',**kwargs)
                else:
                    self.write_file(func,f'#内置函数or类实例化调用\n',**kwargs)
                    self.main_tree[-1]["call_list"] = Call.args
                    SF = System_function(self.main_tree,func_name,func,**kwargs)
                    x = SF.main(**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
                    self.write_file(func,f'##  调用结束\n',**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} main_tree[-1].call_list[-1]\n',**kwargs)
                    return x
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} main_tree[-1].call_list[-1]\n',**kwargs)
                if not kwargs.get("ClassName"):
                    for i in self.main_tree[0]["functions"]:
                        if i["id"] == func_name:
                            return [None,i["type"]]
                return [None,None]
            elif isinstance(Call.func,ast.Attribute):
                
                ## 属性处理
                attribute_name = None
                if isinstance(Call.func.value,ast.Name):
                    attribute_name = Call.func.value.id
                func_name = Call.func.attr
                
                #函数参数赋值
                args = self.get_function_args(func_name,**kwargs)
                call_name = self.get_function_call_name(func_name,**kwargs)
                if(attribute_name!='mc' and not self.py_check_type_is_mc(attribute_name)):
                    
                    self.write_file(func,f'\n##函数调用_begin\n',**kwargs)
                    self.write_file(func,f'#参数处理.函数处理\n',**kwargs)
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','append',[],func,**kwargs)
                    self.main_tree[-1]["call_list"] = []
                    #位置传参
                    for i in range( len(Call.args)):
                        self.Expr_set_value(ast.Assign(targets=[ast.Name(id=None)],value=Call.args[i]),func,**kwargs)
                    #关键字传参
                    for i in range(len(Call.keywords)):
                        if isinstance(Call.keywords[i],ast.keyword):
                            self.Expr_set_value(ast.Assign(targets=[ast.Name(id=Call.keywords[i].arg)],value=Call.keywords[i].value),func,**kwargs)
                    self.mcf_new_stack(func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list','set',f'storage {defualt_STORAGE} main_tree[-2].call_list',func,**kwargs)
                    #判断是否为第三方数据包
                    SF = Custom_function(self.main_tree,attribute_name,func_name,**kwargs)
                    x = [None,None]
                    result = [None,None]
                    if not SF.main(func,**kwargs):
                        
                        self.main_tree[-1]["call_list"] = Call.args
                        x:list = self.AttributeHandler(Call.func,func,True,**kwargs)
                        
                        self.main_tree[-1]["call_list"] = Call.args
                        if len(x) == 2:
                            try:
                                Handler = TypeAttributeHandler(self.main_tree,x[0][0]["value"],x[0][0]["type"],func_name,None,True,storage = x[1])
                                result = Handler.main(func,**kwargs)
                            except:
                                Handler = TypeAttributeHandler(self.main_tree,x[0][0],x[0][1],func_name,None,True,storage = x[1])
                                result = Handler.main(func,**kwargs)
                        elif len(x) >= 3 and x[2].get("haveCallFunc"):
                            result = x[0:2]
                        else:
                            
                            Handler = TypeAttributeHandler(self.main_tree,x[0],self.check_type(x[1]),func_name,None,True)
                            x = Handler.main(func,**kwargs)
                        
                    self.mcf_remove_stack_data(func,**kwargs)
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} main_tree[-1].call_list[-1]\n',**kwargs)
                    return result
                else:
                    
                    ## mc内置
                    self.main_tree[-1]["call_list"] = Call.args
                    MCF =  mc_function(self.main_tree)
                    x = MCF.main(func_name,self.main_tree[-1]["call_list"],func,attribute_name=self.py_return_type_mc(attribute_name),var=attribute_name,**kwargs)
                    return x
        elif isinstance(Call , ast.Attribute):
            #属性 (类)
            self.mcf_new_stack(func,**kwargs)
            x = [None,None]
            if not isinstance(Call.value,ast.Call):
                
                ClassC = ClassCall(self.main_tree,**kwargs)
                StoragePath = ClassC.class_var_to_str(Call,func,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].return','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].return[-1].value','set',f'{StoragePath}',func,**kwargs)
            else:
                x:list = self.AttributeHandler(Call,func,True,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].return','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].return[-1].value','set',f'{x[1].replace("return[-1]","return[-2]")}',func,**kwargs)
            # self.mcf_remove_stack_data(func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} main_tree[-1].call_list[-1]\n',**kwargs)
            return x
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} main_tree[-1].call_list[-1]\n',**kwargs)
        return [None,None]
# 调用函数时 参数处理器
    def Expr_set_value(self,tree:ast.Assign,func,loopTime=0,*args,**kwargs):
        '''函数调用 传参\n
        参数处理'''
        # 类型扩建TODO
        if isinstance(tree.value,ast.BinOp):
            tree.value = self.BinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    # self.py_change_value(i.id,tree.value.value,False,func,False,-1)
                    if (tree.value.kind == None):
                        self.mcf_add_exp_operation(tree.value.value,func,-1,**kwargs)
                        self.py_call_list_append(-1,{"value":tree.value.value,"id":i.id,"is_constant":True})
                    else:
                        self.py_call_list_append(-1,{"value":tree.value.value,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value','set',f'storage {defualt_STORAGE} main_tree[{-1}].exp_operation[-1].value',func,**kwargs)
            self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_call_list_append(-1,{"value":tree.value.value,"id":i.id,"is_constant":True})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1]','append',{"value":tree.value.value,"id":f"{i.id}"},func,**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_call_list_append(-1,{"value":self.py_get_value(tree.value.id,func,False,-1,**kwargs),"id":i.id,"is_constant":False},**kwargs)
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.value.id}"}}].value',func,**kwargs)
        elif isinstance(tree.value,ast.BoolOp):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    #
                    self.main_tree[-1]['condition_time'] += 1
                    self.mcf_new_stack(func,**kwargs)
                    self.mcf_new_stack_inherit_data(func,**kwargs)
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                    kwargs_ = copy.deepcopy(kwargs)
                    kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                    kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['Is_new_function'] = False
                    self.BoolOp(tree.value,0,func,True,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                    self.BoolOp_operation(tree.value,0,0,func,**kwargs)
                    kwargs = kwargs_
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[-2].call_list[-1][-1].value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Compare):
            self.Compare_call(tree.value,func,**kwargs)
            # python 赋值 主要是查是否为全局变量
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-2].call_list[-1][-1].value','int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.UnaryOp):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.mcf_new_stack(func,**kwargs)
                    self.mcf_new_stack_inherit_data(func,**kwargs)
                    self.main_tree[-1]['condition_time'] += 1
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                    self.UnaryOp(tree.value,True,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                    self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-2].call_list[-1][-1].value','int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.Subscript(tree.value,func,**kwargs)
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value',func,**kwargs)
        elif isinstance(tree.value,ast.Call):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    # 函数返回值 赋值
                    self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
        elif isinstance(tree.value,ast.Attribute):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    ClassC = ClassCall(self.main_tree,**kwargs)
                    StoragePath = ClassC.class_var_to_str(tree.value,func,**kwargs)
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value','set',f'{StoragePath}',func,**kwargs)
        elif isinstance(tree.value,ast.List):
            self.List(tree.value,func,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1]','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].list_handler',func,**kwargs)
# 返回值
    def Return(self,tree:ast.Return,func,*args,**kwargs):
        '''函数返回值处理'''
        # 类型扩建TODO
        self.write_file(func,f'##函数返回值处理_bengin\n',**kwargs)
        if isinstance(tree.value,ast.BinOp):
            value = self.BinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(value.value)
            if (value.kind == None):
                self.mcf_add_exp_operation(value.value,func,-1,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set from storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value\n',**kwargs)
            self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(tree.value.value)
            value = tree.value.value
            if isinstance(value,str):
                value = "\""+str(value)+"\""
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":{value}}}\n',**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(self.py_get_value(tree.value.id,func,-1))
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.value.id}"}}].value\n',**kwargs)
        elif isinstance(tree.value,ast.Call):
            value = self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(self.py_get_value(value[0],func,-1))
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].return append from storage {defualt_STORAGE} main_tree[-1].return[-1]\n',**kwargs)
        elif isinstance(tree.value,ast.BoolOp):
            self.BoolOP_call(tree.value,func,**kwargs)
            #
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-3].return','append',{"value":0},func,**kwargs)
            self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[-3].return[-1].value',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(0)
        elif isinstance(tree.value,ast.Compare):
            self.Compare_call(tree.value,func,**kwargs)
            #
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-3].return','append',{"value":0},func,**kwargs)
            self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-3].return[-1].value','int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.UnaryOp):
            self.mcf_new_stack(func,**kwargs)
            self.mcf_new_stack_inherit_data(func,**kwargs)
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            self.UnaryOp(tree.value,True,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
            #
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-3].return','append',{"value":0},func,**kwargs)
            self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-3].return[-1].value','int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(0)
            self.Subscript(tree.value,func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-2].return[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value',func,**kwargs)
        self.mcf_stack_return(func,**kwargs)
        self.write_file(func,f'##函数返回值处理_end\n',**kwargs)
# 切片
    def Subscript(self,tree:ast.Subscript,func,*args,**kwargs):
        '''切片处理'''
        # 类型扩建TODO
        if isinstance(tree.value,ast.Subscript):
            self.Subscript(tree.value,func,**kwargs)
            self.Subscript_index(tree.slice,func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value\n',**kwargs)
            self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/start\n',**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value set from storage t_algorithm_lib:array get_element_by_index.list2[0]\n',**kwargs)
        else:
            if isinstance(tree.value,ast.Call):
                # 函数返回值
                self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
                self.Subscript_index(tree.slice,func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].return[-1].value\n',**kwargs)
                self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/start\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value set from storage t_algorithm_lib:array get_element_by_index.list2[0]\n',**kwargs)
            elif isinstance(tree.value,ast.Name):
                # 变量
                self.Subscript_index(tree.slice,func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":{tree.value.id}}}].value\n',**kwargs)
                self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/start\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value set from storage t_algorithm_lib:array get_element_by_index.list2[0]\n',**kwargs)
            elif isinstance(tree.value,ast.BinOp):
                # 运算
                self.Subscript_index(tree.slice,func,**kwargs)
                tree.value = self.BinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
                if (tree.value.kind == None):
                    self.mcf_add_exp_operation(tree.value.value,func,-1)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value\n',**kwargs)
                self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/start\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value set from storage t_algorithm_lib:array get_element_by_index.list2[0]\n',**kwargs)
                self.mcf_remove_Last_exp_operation(func,**kwargs)
            elif isinstance(tree.value,ast.Constant):
                self.Subscript_index(tree.slice,func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":{tree.value.value}}}].value\n',**kwargs)
                self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/start\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value set from storage t_algorithm_lib:array get_element_by_index.list2[0]\n',**kwargs)
            elif isinstance(tree.value,ast.List):
                self.List(tree.value,func,**kwargs)
                self.Subscript_index(tree.slice,func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].list_handler\n',**kwargs)
                self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/start\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value set from storage t_algorithm_lib:array get_element_by_index.list2[0]\n',**kwargs)
# 切片指针处理器
    def Subscript_index(self,tree:ast.Index,func,*args,**kwargs):
        # 类型扩建TODO
        if isinstance(tree.value,ast.Subscript):
            self.Subscript(tree.value,func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #tal.array.get_element_by_index.index tal.input run data get storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value\n',**kwargs)
        elif isinstance(tree.value,ast.Name):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #tal.array.get_element_by_index.index tal.input run data get storage {defualt_STORAGE} main_tree[-1].data[{{"id":{tree.value.id}}}].value\n',**kwargs)
        elif isinstance(tree.value,ast.Call):
            self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #tal.array.get_element_by_index.index tal.input run data get storage {defualt_STORAGE} main_tree[-1].return[-1].value\n',**kwargs)
        elif isinstance(tree.value,ast.BinOp):
            tree.value = self.BinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
            if (tree.value.kind == None):
                self.mcf_add_exp_operation(tree.value.value,func,-1,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #tal.array.get_element_by_index.index tal.input run data get storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value\n',**kwargs)
            self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            self.write_file(func,f'scoreboard players set #tal.array.get_element_by_index.index tal.input {tree.value.value}\n',**kwargs)
        elif isinstance(tree.value,ast.List):
                self.List(tree.value,func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #tal.array.get_element_by_index.index tal.input run data get storage {defualt_STORAGE} main_tree[-1].list_handler\n',**kwargs)

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
        self.main_tree[-1]["record_condition"] = []
        if mode:
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/call',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.end {scoreboard_objective} matches 0 run ',**kwargs)
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
        else:
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/call',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.end {scoreboard_objective} matches 0 run ',**kwargs)
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
        kwargs['f2'] = f'call'
        kwargs['Is_new_function'] = False
        self.write_file(func,f'#\n',**kwargs)
        # 类型扩建TODO
        if isinstance(tree.test,ast.BoolOp):
            self.main_tree[-1]['condition_time'] += 1
            if mode:
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                kwargs['Is_new_function'] = False
                self.BoolOp(tree.test,condition_time+1,func,mode,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.BoolOp_operation(tree.test,1,0,func,**kwargs)
                
            else:
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)

                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                kwargs['Is_new_function'] = False
                
                self.BoolOp(tree.test,condition_time+1,func,False,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.BoolOp_operation(tree.test,1,0,func,**kwargs)
        if isinstance(tree.test,ast.BinOp):
            self.main_tree[-1]['condition_time'] += 1
            if mode:
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                kwargs['Is_new_function'] = False
                self.BinOp(tree.test,tree.test.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                self.mcf_remove_Last_exp_operation(func,**kwargs)
            else:
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                kwargs['Is_new_function'] = False
                self.BinOp(tree.test,tree.test.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.test,ast.Compare):
            self.main_tree[-1]['condition_time'] += 1
            if mode:
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                self.Compare(tree.test,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            else:
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                self.Compare(tree.test,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
        elif isinstance(tree.test,ast.UnaryOp):
            self.main_tree[-1]['condition_time'] += 1
            if mode:
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                self.UnaryOp(tree.test,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
            else:
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
                self.UnaryOp(tree.test,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
        elif isinstance(tree.test,ast.Name):
            self.main_tree[-1]['condition_time'] += 1

            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.test.id}"}}].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Call):
            self.main_tree[-1]['condition_time'] += 1
            self.Expr(ast.Expr(value=tree.test),func,-1,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].return[-1].value\n',**kwargs)
        elif isinstance(tree.test,ast.Attribute):
            ClassC = ClassCall(self.main_tree,**kwargs)
            StoragePath = ClassC.class_var_to_str(tree.test,func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get {StoragePath}\n',**kwargs)
        elif isinstance(tree.test,ast.Constant):
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":tree.test.value},func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Subscript):
            self.main_tree[-1]['condition_time'] += 1
            self.Subscript(tree.test,func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        #body
        kwargs = copy.deepcopy(kwargs_)
        self.write_file(func,f'#\n',**kwargs)
        if not only_test:
            if mode:
                #调用
                kwargs['ClassName'] = kwargs.get("ClassName")
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run ',**kwargs)
                # end if
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.end {scoreboard_objective} 1\n',p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'main',ClassName=kwargs.get("ClassName"))
                kwargs['Is_new_function'] = False
                self.walk(tree.body,func,-1,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'main',ClassName=kwargs.get("ClassName"))
            else:
                #调用
                kwargs['ClassName'] = kwargs.get("ClassName")
                self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run ',**kwargs)
                # end if
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.end {scoreboard_objective} 1\n',p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'main',ClassName=kwargs.get("ClassName"))
                kwargs['Is_new_function'] = False
                self.walk(tree.body,func,-1,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'main',ClassName=kwargs.get("ClassName"))
            if len(tree.orelse) >0:
                kwargs = kwargs_
                if isinstance(tree.orelse[0],ast.If) and len(tree.orelse) ==1:
                #elif
                    kwargs['ClassName'] = kwargs.get("ClassName")
                    self.main_tree[-1]['elif_time'] += 1
                    self.main_tree[-1]['condition_time'] = 0
                    self.If(tree.orelse[0],0,func,False,ClassName=kwargs.get("ClassName"),**kwargs)
                else:
                    kwargs['ClassName'] = kwargs.get("ClassName")
                    self.write_file(func,f'#\n',**kwargs)
                        #调用 else
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/else/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 run ',**kwargs)
                    # kwargs['Is_new_function'] = False
                    self.walk(tree.orelse,func,-1,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//else//',f2=f'main',ClassName=kwargs.get("ClassName"))

# 布尔运算
    def BoolOp(self,tree:ast.BoolOp,condition_time:0,func:str,mode:bool = True,*args,**kwargs):
        '''逻辑运算 and or \n mode为else'''
        for item in tree.values:
            # 类型扩建TODO
            if isinstance(item,ast.BoolOp):
                self.main_tree[-1]['condition_time'] += 1
                if mode:
                    
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_operation(item,self.main_tree[-1]["condition_time"],condition_time,func,**kwargs)
                    self.BoolOp(item,self.main_tree[-1]["condition_time"],func,mode,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_operation(item,self.main_tree[-1]["condition_time"],condition_time,func,**kwargs)
                    self.BoolOp(item,condition_time,func,mode,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            elif isinstance(item,ast.Compare):
                self.main_tree[-1]['condition_time'] += 1
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
                    self.Compare(item,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                    
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
                    self.Compare(item,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            elif isinstance(item,ast.UnaryOp):
                self.main_tree[-1]['condition_time'] += 1
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
                    self.UnaryOp(item,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
                    self.UnaryOp(item,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            elif isinstance(item,ast.Name):
                self.main_tree[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{item.id}"}}].value',func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run scoreboard players operation #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} = #{defualt_NAME}.sys.c.{condition_time}.pass {scoreboard_objective}\n',**kwargs)
                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
            elif isinstance(item,ast.Constant):
                self.main_tree[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                
                self.mcf_reset_score(f'#{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}',func,**kwargs)
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} {item.value}\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} 1\n',**kwargs)
                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
            elif isinstance(item,ast.BinOp):
                self.main_tree[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                
                self.BinOp(item,item.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
                self.mcf_remove_Last_exp_operation(func,**kwargs)
            elif isinstance(item,ast.Subscript):
                self.main_tree[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                else:
                    self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}',func,prefix=self.BoolOp_get_prefix(tree,condition_time,func,**kwargs),**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                
                self.Subscript(item,func,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)

                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
# 比较
    def Compare(self,tree:ast.Compare,condition_time:0,func:str,*args,**kwargs):
        '''判断语句 > < == != >= <='''
        #左
        # 类型扩建TODO
        if isinstance(tree.left,ast.BinOp):
            self.BinOp(tree.left,tree.left.op,func,-1,-1,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
            self.mcf_remove_Last_exp_operation(func,**kwargs)
        elif isinstance(tree.left,ast.Constant):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":tree.left.value},func,**kwargs)
        elif isinstance(tree.left,ast.Name):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.left.id}"}}].value',func,**kwargs)
        elif isinstance(tree.left,ast.Call):
            # 函数返回值 赋值
            self.Expr(ast.Expr(value=tree.left),func,-1,**kwargs)
            # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',f'storage {defualt_STORAGE} main_tree[-1].return[-1]',func,**kwargs)
        #右
        # 类型扩建TODO
        for item in tree.comparators:
            if isinstance(item,ast.BinOp):
                self.BinOp(item,item.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.mcf_remove_Last_exp_operation(func,**kwargs)
            elif isinstance(item,ast.Constant):
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":item.value},func,**kwargs)
            elif isinstance(item,ast.Name):
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.left.id}"}}].value',func,**kwargs)
            elif isinstance(item,ast.Call):
            # 函数返回值 赋值
                self.Expr(ast.Expr(value=item),func,-1,**kwargs)
                # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
        #再根据判断类型 > < >= <= != ==
        for item in tree.ops:
            if isinstance(item,ast.cmpop):
                self.mcf_reset_score(f'#{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}',func,**kwargs)
                self.mcf_compare_Svalues(f'{defualt_STORAGE} main_tree[-1].boolOPS[-2].value',f'{defualt_STORAGE} main_tree[-1].boolOPS[-1].value',item,func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} 1',**kwargs)
# 布尔 and/or
    def BoolOp_operation(self,tree:ast.BoolOp,condition_time:int,condition_time2:int,func:str,*args,**kwargs):
        '''逻辑运算中 and or'''
        if isinstance(tree.op,ast.And):
            self.write_file(func,f'##和\nscoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\nexecute if score #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} = #{defualt_NAME}.sys.c3.{condition_time} {scoreboard_objective2} run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            #
        elif isinstance(tree.op,ast.Or):
            self.write_file(func,f'##或\nscoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\nexecute if score #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
# 记录 运算后的布尔值
    def BoolOp_record(self,tree:ast.BoolOp,condition_time:int,index:int,func:str,*args,**kwargs):
        '''逻辑运算中 记录逻辑结果'''

        #统计该情况下的所有逻辑判断
        
        # 判断是否初始化过
        flag = self.BoolOp_check_has_init(condition_time,func,**kwargs)
        if not flag:
            self.write_file(func,f'scoreboard players add #{defualt_NAME}.sys.c3.{condition_time} {scoreboard_objective2} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{index} {scoreboard_objective} matches 1 run scoreboard players add #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} 1\n',**kwargs)
        else:
            pre = ''
            if isinstance(tree.op,ast.And):
                pre = f'execute unless score #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} = #{defualt_NAME}.sys.c3.{condition_time} {scoreboard_objective2} run '
            elif isinstance(tree.op,ast.Or):
                pre = f'execute unless score #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} matches 1.. run '
            self.write_file(func,f'{pre}scoreboard players add #{defualt_NAME}.sys.c3.{condition_time} {scoreboard_objective2} 1\n',**kwargs)
            self.write_file(func,f'{pre}execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{index} {scoreboard_objective} matches 1 run scoreboard players add #{defualt_NAME}.sys.c2.{condition_time} {scoreboard_objective2} 1\n',**kwargs)

    def BoolOp_check_has_init(self,condition_time,func,*args,**kwargs)->bool:
        '''判断是否已经初始化'''
        if not(condition_time in self.main_tree[-1]["record_condition"]):
            self.main_tree[-1]["record_condition"].append(condition_time)
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
        self.main_tree[-1]['condition_time'] += 1
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
        kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
        kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
        kwargs['Is_new_function'] = False
        self.BoolOp(value,0,func,True,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
        self.BoolOp_operation(value,0,0,func,**kwargs)

    def Compare_call(self,value:ast.Compare,func:str,*args,**kwargs):
        """Compare调用\n
        返回处理\n 
        self.mcf_store_value_by_run_command(f'{}','int 1'f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
        """
        self.main_tree[-1]['condition_time'] += 1
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
        self.Compare(value,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
        self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
        

    def UnaryOp_call(self,value:ast.UnaryOp,func:str,*args,**kwargs):
        """UnaryOp调用"""
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.main_tree[-1]['condition_time'] += 1
        self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
        self.UnaryOp(value,True,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
        self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)

##

# 一元操作(目前有：取反)
    def UnaryOp(self,tree:ast.UnaryOp,mode:bool,condition_time:0,func:str,*args,**kwargs):
        '''条件 一元运算符 '''
        self.write_file(func,f'scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        # self.If(ast.If(test=tree.operand,body=[],orelse=[]),condition_time,func,mode,only_test=True,**kwargs)
        ## 取反
        # 类型扩建TODO
        if isinstance(tree.operand,ast.BoolOp):
            if mode:
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                kwargs['Is_new_function'] = False
                self.BoolOp(tree.operand,condition_time+1,func,mode,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.BoolOp_operation(tree.operand,0,0,func,**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                kwargs['Is_new_function'] = False
                
                self.BoolOp(tree.operand,condition_time+1,func,False,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.BoolOp_operation(tree.operand,0,0,func,**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
        if isinstance(tree.operand,ast.BinOp):
            if mode:
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                kwargs['Is_new_function'] = False
                self.BinOp(tree.operand,tree.operand.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                self.mcf_remove_Last_exp_operation(func,**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                kwargs['Is_new_function'] = False
                self.BinOp(tree.operand,tree.operand.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                self.mcf_remove_Last_exp_operation(func,**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Compare):
            if mode:
                self.Compare(tree.operand,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                self.Compare(tree.operand,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.UnaryOp):
            if mode:
                self.UnaryOp(tree.operand,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                self.UnaryOp(tree.operand,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
                #取反
                self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Name):

            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.operand.id}"}}].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            #取反
            self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Constant):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":tree.operand.value},func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            #取反
            self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Subscript):
            self.Subscript(tree.operand,func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            #取反
            self.get_condition_reverse(func,**kwargs)
# 条件取反
    def get_condition_reverse(self,func,*args,**kwargs):
        '''条件取反'''
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass_ {scoreboard_objective} 0\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass_ {scoreboard_objective} 1\n',**kwargs)
        self.mcf_reset_score(f'#{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}',func,**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run scoreboard players operation #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass_ {scoreboard_objective}\n',**kwargs)

## 循环模块
# while
    def While(self,tree:ast.While,func:str,*args,**kwargs):
        '''While循环处理'''
        self.main_tree[-1]["while_time"] += 1
        # test
        ## while前 新建栈
        self.write_file(func,f'     ##while_begin   \n',**kwargs)
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.mcf_call_function(f'{func}/while_{self.main_tree[-1]["while_time"]}/_start',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        self.mcf_old_stack_cover_data(func,**kwargs)
        self.mcf_remove_stack_data(func,**kwargs)
        self.write_file(func,f'     ##while_end     \n',**kwargs)

        kwargs_ = copy.deepcopy(kwargs)
        kwargs['Is_new_function'] = False
        kwargs['p'] = f'{func}//while_{self.main_tree[-1]["while_time"]}//'
        kwargs['f2'] = f'_start'
        ## is_continue
        self.write_file(func,f'execute if data storage {defualt_STORAGE} main_tree[-1].is_continue run scoreboard players reset #{defualt_STORAGE}.stack.end {scoreboard_objective}\n',**kwargs)
        self.write_file(func,f'execute if data storage {defualt_STORAGE} main_tree[-1].is_continue run data remove storage {defualt_STORAGE} main_tree[-1].is_continue\n',**kwargs)
        #
        self.mcf_call_function(f'{func}/while_{self.main_tree[-1]["while_time"]}/condition/_start',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        

        kwargs['p'] = f'{func}//while_{self.main_tree[-1]["while_time"]}//condition//'
        # 类型扩建TODO
        if isinstance(tree.test,ast.Name):
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.main_tree[-1]['condition_time'] = 0
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.test.id}"}}].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Call):
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.main_tree[-1]['condition_time'] = 0
            self.main_tree[-1]['condition_time'] += 1
            self.Expr(ast.Expr(value=tree.test),func,-1,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].return[-1].value\n',**kwargs)

        elif isinstance(tree.test,ast.UnaryOp):
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.main_tree[-1]['condition_time'] = 1
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            self.UnaryOp(tree.test,True,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
        elif isinstance(tree.test,ast.Constant):
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.main_tree[-1]['condition_time'] = 0
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":tree.test.value},func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Compare):
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.main_tree[-1]['condition_time'] = 0
            self.Compare_call(tree.test,func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            self.main_tree[-1]['condition_time'] = 0
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.test,ast.BoolOp):
            self.main_tree[-1]['condition_time'] = 0
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            self.BoolOp(tree.test,1,func,True,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}',ClassName=kwargs.get("ClassName"))
            self.BoolOp_operation(tree.test,0,0,func,**kwargs)
            self.main_tree[-1]['condition_time'] = 0
        elif isinstance(tree.test,ast.Subscript):
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.main_tree[-1]['condition_time'] += 1
            self.Subscript(tree.test,func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.BinOp):
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_call_function(f'{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}',func,prefix=f"execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ",**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['Is_new_function'] = False
            self.BinOp(tree.test,tree.test.op,func,-1,-1,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            self.mcf_remove_Last_exp_operation(func,**kwargs)
        # body
        kwargs['p'] = f'{func}//while_{self.main_tree[-1]["while_time"]}//'
        kwargs['f2'] = f'_start'
        self.write_file(func,f'##while 主程序\n',**kwargs)

        self.mcf_call_function(f'{func}/while_{self.main_tree[-1]["while_time"]}/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if score #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run ',**kwargs)
        temp_value = self.main_tree[-1]["while_time"]
        self.walk(tree.body,func,-1,p=f'{func}//while_{self.main_tree[-1]["while_time"]}//',f2=f'main',ClassName=kwargs.get("ClassName"))

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
        self.main_tree[-1]["for_time"] += 1
        
        # test
        ## for前 新建栈
        
        self.write_file(func,f'    ##for_begin   \n',**kwargs)
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.mcf_call_function(f'{func}/for_{self.main_tree[-1]["for_time"]}/_start',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        self.mcf_old_stack_cover_data(func,**kwargs)
        self.mcf_remove_stack_data(func,**kwargs)
        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"temp":1b}}]','remove','',func,**kwargs)
        self.write_file(func,f'    ##for_end     \n',**kwargs)

        kwargs_ = copy.deepcopy(kwargs)

        kwargs['Is_new_function'] = False
        kwargs['p'] = f'{func}//for_{self.main_tree[-1]["for_time"]}//'
        kwargs['f2'] = f'_start'
        ##初始化 迭代器列表
        self.write_file(func,f'#迭代器初始化\n',**kwargs)
        self.mcf_call_function(f'{func}/for_{self.main_tree[-1]["for_time"]}/iterator/_init',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        ## is_continue
        kwargs['f2'] = f'main'
        self.write_file(func,f'execute if data storage {defualt_STORAGE} main_tree[-1].is_continue run scoreboard players reset #{defualt_STORAGE}.stack.end {scoreboard_objective}\n',**kwargs)
        self.write_file(func,f'execute if data storage {defualt_STORAGE} main_tree[-1].is_continue run data remove storage {defualt_STORAGE} main_tree[-1].is_continue\n',**kwargs)
        #
        self.mcf_call_function(f'{func}/for_{self.main_tree[-1]["for_time"]}/iterator/_start',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        kwargs['p'] = f'{func}//for_{self.main_tree[-1]["for_time"]}//iterator//'
        if isinstance(tree.target,ast.Name):
            kwargs['f2'] = f'_start'
            kwargs['p'] = f'{func}//for_{self.main_tree[-1]["for_time"]}//iterator//'
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.target.id}","temp":1b}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].for_list[0].value',func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].for_list[0]','remove','',func,**kwargs)
            if isinstance(tree.iter,ast.Call):
                kwargs['f2'] = f'_init'
                kwargs['p'] = f'{func}//for_{self.main_tree[-1]["for_time"]}//iterator//'
                # 函数返回值 赋值
                self.Expr(ast.Expr(value=tree.iter),func,-1,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].for_list','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)

        # body
        kwargs['p'] = f'{func}//for_{self.main_tree[-1]["for_time"]}//'
        kwargs['f2'] = f'_start'
        self.write_file(func,f'##for 主程序\n',**kwargs)
        self.mcf_call_function(f'{func}/for_{self.main_tree[-1]["for_time"]}/main',func,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        temp_value = self.main_tree[-1]["for_time"]
        ## 
        
        self.walk(tree.body,func,-1,p=f'{func}//for_{self.main_tree[-1]["for_time"]}//',f2=f'main',ClassName=kwargs.get("ClassName"))
        self.mcf_call_function(f'{func}/for_{temp_value}/main',func,p=f'{func}//for_{temp_value}//',f2=f'main',ClassName=kwargs.get("ClassName"),prefix = f'execute if data storage {defualt_STORAGE} main_tree[-1].for_list[0] run ')
        ##

##

# list
    def List(self,tree:ast.List,func:str,loop_time=0,*args,**kwargs):
        ''''列表 处理'''
        if loop_time==0:
            self.main_tree[-1]["list_handler"] = []
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].list_handler','set',[],func,**kwargs)
        if len(tree.elts) == 0:
            self.main_tree[-1]["list_handler"].append()
            text = '[-1]'*loop_time
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].list_handler{text}','append',[],func,**kwargs)
        for item in tree.elts:
            if isinstance(item,ast.BinOp):
                value = self.BinOp(item,item.op,func,-1,-1,**kwargs)
                if value.kind[0] != 'is_v':
                    self.main_tree[-1]["list_handler"].append(value.value)
                else:
                    self.main_tree[-1]["list_handler"].append(None)
                text = '[-1]'*loop_time
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].list_handler{text}','append',[],func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].list_handler[-1]{text}','append',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.mcf_remove_Last_exp_operation(func,**kwargs)
            elif isinstance(item,ast.Constant):
                    self.main_tree[-1]["list_handler"].append(item.value)
                    text = '[-1]'*loop_time
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].list_handler{text}','append',[item.value],func,**kwargs)
            elif isinstance(item,ast.Name):
                self.py_get_value(item.id,func,-1,**kwargs)
                self.main_tree[-1]["list_handler"].append(None)
                text = '[-1]'*loop_time
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].list_handler{text}','append',[],func,**kwargs)
                IsGlobal = self.py_get_value_global(item.id,func,-1,**kwargs)
                if IsGlobal:
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].list_handler[-1]{text}','append',f'storage {defualt_STORAGE} main_tree[0].data[{{"id":"{item.id}"}}].value',func,**kwargs)
                else:
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].list_handler[-1]{text}','append',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{item.id}"}}].value',func,**kwargs)
            elif isinstance(item,ast.Subscript):
                # 切片赋值
                self.Subscript(item,func,**kwargs)
                self.main_tree[-1]["list_handler"].append(None)
                text = '[-1]'*loop_time
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].list_handler{text}','append',[],func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].list_handler[-1]{text}','append',f'storage {defualt_STORAGE} main_tree[-1].Subscript[-1].value',func,**kwargs)
            elif isinstance(item,ast.Call):
                # 函数返回值 赋值
                self.Expr(ast.Expr(value=item),func,-1,**kwargs)
                # python 赋值 主要是查是否为全局变量
                self.main_tree[-1]["list_handler"].append(None)
                text = '[-1]'*loop_time
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].list_handler{text}','append',[],func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].list_handler[-1]{text}','append',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
            elif isinstance(item,ast.BoolOp):
                self.BoolOP_call(item,func,**kwargs)
                # python 赋值 主要是查是否为全局变量
                self.main_tree[-1]["list_handler"].append(None)
                text = '[-1]'*loop_time
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].list_handler{text}','append',[],func,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].list_handler[-1]{text}','append',0,func,**kwargs)
                self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[-2].list_handler[-1]{text}',f'#{defualt_NAME}.sys.c.0.pass {scoreboard_objective}','int','1',func,**kwargs)
                self.mcf_remove_stack_data(func,**kwargs)
            elif isinstance(item,ast.Compare):
                self.Compare_call(item,func,**kwargs)
                self.main_tree[-1]["list_handler"].append(None)
                text = '[-1]'*loop_time
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].list_handler{text}','append',[],func,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].list_handler[-1]{text}','append',0,func,**kwargs)
                self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-2].list_handler[-1]{text}',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                self.mcf_remove_stack_data(func,**kwargs)
            elif isinstance(item,ast.UnaryOp):
                self.UnaryOp_call(item,func,**kwargs)
                self.main_tree[-1]["list_handler"].append(None)
                text = '[-1]'*loop_time
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].list_handler{text}','append',[],func,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].list_handler[-1]{text}','append',0,func,**kwargs)
                self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-2].list_handler[-1]{text}',f'int 1',f'scoreboard players get #{defualt_NAME}.sys.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                self.mcf_remove_stack_data(func,**kwargs)
            elif isinstance(item,ast.List):
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].list_handler{text}','append',[[]],func,**kwargs)
                self.List(item,func,loop_time+2,**kwargs)

# 属性处理
    def AttributeHandler(self,tree:ast.Attribute,func:str,IsCallFuc=False,inputData='',*args,**kwargs):
        '''属性处理
        IsCallFuc=False:调用属性的值
        IsCallFuc=True:为调用属性方法
        '''
        
        ReturnValue= [None,None,None,None]
        
        if isinstance(tree.value,ast.Attribute):
            ReturnData = self.AttributeHandler(tree.value,func,False,**kwargs)
            ReturnValue = ReturnData[0]
            inputData = ReturnData[1]
            if not IsCallFuc:
                ReturnValue[0] = self.py_get_var_info(tree.attr,ReturnData[0][0]["value"])
                inputData += f'[{{"id":"{tree.attr}"}}].value'
            return ReturnValue,inputData

        elif isinstance(tree.value,ast.Call):
            inputData = f'storage {defualt_STORAGE} main_tree[-1].return[-1].value[{{"id":"{tree.attr}"}}].value'
            ReturnValue = self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            return ReturnValue,inputData
        elif isinstance(tree.value,ast.Name):
            # 查类型
            # 根据 类型 调用属性
            if not IsCallFuc:
                inputData = f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.value.id}"}}].value[{{"id":"{tree.attr}"}}].value'
                x = self.py_get_var_info(tree.value.id,self.main_tree[-1]["data"])
                ReturnValue= [None,None,None,None]
                ReturnValue[0] = self.py_get_var_info(tree.attr,x["value"])
                ClassC = ClassCall(self.main_tree,**kwargs)
                var = ClassC.get_class_var(tree,func,**kwargs)
                value = var.get('value')
                type = var.get('type')
                return ReturnValue,inputData
            if IsCallFuc:
                var = self.py_get_var_info(tree.value.id,self.main_tree[0]["data"])
                ##判断是否为类的名称
                if var == None:
                    var = {"id":tree.value.id,"type":None,"value":None}
                    for i in self.main_tree[0]["class_list"]:
                        if i["id"] == tree.value.id:
                            var = {"id":tree.value.id,"type":i["id"],"value":None}
                
                Handler = TypeAttributeHandler(self.main_tree,var["value"],var["type"],tree.attr,var["id"],IsCallFuc)
                ReturnValue:list = Handler.main(func,**kwargs)
                ReturnValue.append({"newName":tree.attr})

        # else:
        #     Handler = TypeAttributeHandler(self.main_tree,ReturnValue[0],self.check_type(ReturnValue[1]),tree.attr,None,IsCallFuc)
        #     ReturnValue = Handler.main(func,**kwargs)
        if not IsCallFuc:
            if not isinstance(tree.value,(ast.Name,ast.Call)):
                Handler = TypeAttributeHandler(self.main_tree,ReturnValue[0],self.check_type(ReturnValue[1]),tree.attr,None,IsCallFuc)
                ReturnValue = Handler.main(func,**kwargs)
        
        return ReturnValue

# 类的定义
    def ClassDef(self,tree:ast.ClassDef,func:str,index:-1,*args,**kwargs):
        '''类的定义'''
        self.main_tree[0]["class_list"].append({"id":tree.name,"functions":[]})
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
            self.main_tree,self.func_name,self.func = tuple(args[0:3])
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
                            self.write_file(self.func,f"data modify storage {item['args'][i]['name']} set from storage {defualt_STORAGE} main_tree[-1].call_list[-1][{i}].value\n",**kwargs)
                    self.write_file(self.func,f'#自定义函数调用\n',**kwargs)
                    self.write_file(self.func,f"function {item['call_path']}\n",**kwargs)
                    if item['return']['type'] == 'storage':
                            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return','append',{"value":0},self.func,**kwargs)
                            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-2].return[-1].value','set',f"storage {item['return']['name']}",self.func,**kwargs)
                    IsFind = True
            if not IsFind:
                #如果没找到对应的函数名称，则可能为类的调用
                ClassC = ClassCall(self.main_tree,self.func_name,**kwargs)
                return ClassC.init(self.func,**kwargs)
            else:
                return [None,None]

    def _print(self,func,*args,**kwargs):
        self.write_file(func,f'#参数处理.赋值\n',**kwargs)
        self.write_file(func,f'#自定义函数调用\n',**kwargs)
        self.write_file(func,f'tellraw @a [',**kwargs)
        
        for i in range(len(self.main_tree[-1]["call_list"])):
            value = RawJsonText(MCStorage('storage',f'{defualt_STORAGE}',f'main_tree[-1].call_list[-1][{i}].value'))
            self.write_file(func,f'{value}',func,**kwargs)
            if i >= 0 and i < len(self.main_tree[-1]["call_list"]) - 1:
                self.write_file(func,'," ",',func,**kwargs)
        self.write_file(func,f']\n',**kwargs)
        
        self.write_file(func,f'##函数调用_end\n',**kwargs)
    def _range(self,func,*args,**kwargs):
        self.write_file(func,f'#参数处理.赋值\n',**kwargs)
        self.write_file(func,f'#自定义函数调用\n',**kwargs)
        handle = True
        range_list = []
        for i in self.main_tree[-1]["call_list"]:
            if isinstance(i,ast.Constant):
                range_list.append(i.value)
        if len(range_list) < 2:
            handle = False
        mcf_range_list = []
        if handle:
            for i in range(*range_list):
                mcf_range_list.append({"value":i})
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return','append',{"value":0},self.func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return[-1].value','set',mcf_range_list,self.func,**kwargs)
        else:
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage t_algorithm_lib:array range.input set from storage {defualt_STORAGE} main_tree[-1].call_list[-1][0].value\n',**kwargs)
            self.write_file(func,f'function t_algorithm_lib:array/range/start\n',**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return','append',{"value":0},self.func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return[-1].value','set',[],**kwargs)
        self.write_file(func,f'##函数调用_end\n',**kwargs)
        return [mcf_range_list,"list"]
    def _str(self,func,*args,**kwargs):
        self.write_file(func,f'#自定义函数调用\n',**kwargs)

        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].temp','set','[[1d],[1f],[1l],[1s],[1b]]',self.func,True,**kwargs)
        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-2].temp[]','append',f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value',self.func,**kwargs)
        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return','append',{"value":"None"},self.func,**kwargs)

        self.mcf_build_dynamic_command(
            [f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value'],
            [f'$data modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set value \'$(arg0)\''],
            func,**kwargs)
        self.write_file(func,f'##函数调用_end\n',**kwargs)
        self.write_file(func,f'#判断是否为特殊情况(是否去除末尾)\nexecute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute if data storage {defualt_STORAGE} main_tree[-2].temp[][1] run data modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set string storage {defualt_STORAGE} main_tree[-2].return[-1].value 0 -1\n',**kwargs)
        self.write_file(func,f'data remove storage {defualt_STORAGE} main_tree[-1].call_list[-1]\n',**kwargs)
        
        return ["",'str']
    def _isinstance(self,func,*args,**kwargs):
        if not len(self.main_tree[-1]["call_list"]) >= 2:
            self.write_file(func,f'data remove storage {defualt_STORAGE} main_tree[-1].call_list[-1]\n',**kwargs)
            return [1,'int']
        # 
        storage = ''
        if isinstance(self.main_tree[-1]["call_list"][0],ast.Name):
            storage = f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{self.main_tree[-1]["call_list"][0].id}"}}].type'
        elif isinstance(self.main_tree[-1]["call_list"][0],ast.Attribute):
            ClassC = ClassCall(self.main_tree,**kwargs)
            storage = ClassC.class_var_to_str(i,func,**kwargs)[0:-5] + '.type'
        classList = []
        for i in self.main_tree[-1]["call_list"][1:]:
            if isinstance(i,ast.Constant):
                classList.append(i.value)
            elif isinstance(i,ast.Name):
                classList.append(i.id)
        print("storage",storage)
        self.write_file(func,f'scoreboard players set #{defualt_STORAGE}.stack.t {scoreboard_objective} {len(classList)}\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].temp set value {classList}\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 store result score #{defualt_STORAGE}.stack.t2 {scoreboard_objective} run data modify storage {defualt_STORAGE} main_tree[-2].temp[] set from {storage}\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":0}}\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute unless score #{defualt_STORAGE}.stack.t {scoreboard_objective} = #{defualt_STORAGE}.stack.t2 {scoreboard_objective} run data modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set value 1\n',**kwargs)

        self.write_file(func,f'data remove storage {defualt_STORAGE} main_tree[-1].call_list[-1]\n',**kwargs)
        
        return [1,'int']



# 第三方函数库
class Custom_function(Parser):
    '''自定义(第三方)函数(函数库) 处理器'''
    def __init__(self,*args,**kwargs) -> None:
        '''storage名称 nbt'''
        if len(args) >= 3:
            self.main_tree,self.attribute_name,self.func_name = tuple(args[0:3])
    def main(self,func,*args,**kwargs) -> bool:
        # 系统 函数
        if(self.attribute_name == 'mc'):
            MCF =  mc_function()
            MCF.main(self.func_name,self.main_tree[-1]["call_list"],func,**kwargs)
        # 自定义函数
        for item in custom_functions:
            if item['name'] == self.attribute_name:
                for item2 in item['functions']:
                    if item2['name'] == self.func_name:
                        self.write_file(func,f'#参数处理.赋值\n',**kwargs)
                        for i in range(len(item2['args'])):
                            if item2['args'][i]['type'] == 'storage':
                                self.write_file(func,f"data modify storage {item2['args'][i]['name']} set from storage {defualt_STORAGE} main_tree[-1].call_list[-1][{i}].value\n",**kwargs)
                        self.write_file(func,f'#自定义函数调用\n',**kwargs)
                        self.write_file(func,f"function {item2['call_path']}\n",**kwargs)
                        if item2['return']['type'] == 'storage':
                                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return','append',{"value":0},func,**kwargs)
                                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-2].return[-1].value','set',f"storage {item2['return']['name']}",func,**kwargs)
                        return True
        #无
        return False

# 内置MC函数
class mc_function(Parser):
    '''内置MC函数'''
    def __init__(self,main_tree):
        self.main_tree = main_tree
    def get_value(self,arg:ast,func=None,*args,**kwargs):
        if isinstance(arg,ast.Constant):
            return arg.value
        elif isinstance(arg,ast.Name):
            return self.py_get_value(arg.id,**kwargs)
        elif isinstance(arg,ast.List):
            self.main_tree[-1]["list_handler"] = []
            for item in arg.elts:
                self.main_tree[-1]["list_handler"].append(self.get_value(item))
            return self.main_tree[-1]["list_handler"]
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
                        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].return','append',{"value":0},func,**kwargs)
                        self.write_file(func,f"execute store {flag} storage {defualt_STORAGE} main_tree[-1].return[-1].value double 1.0 run {command}\n",**kwargs)
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
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].return','append',Nbt,func,**kwargs)
                return [str(UUID),mc.MCEntity]
            elif(func_name == 'example'):
                ...
            elif(func_name == 'NewFunction'):
                name = self.get_value(arg[0],func,**kwargs) if len(arg) >= 1 else "load"
                path = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else ""
                self.write_file(name,f"",p=path,f2=name,ClassName=kwargs.get("ClassName"))
                return [True,int]
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
                return [True,int]
            elif(func_name == 'newTags'):
                Tagsname = str(self.get_value(arg[0],func,**kwargs)) + '.json' if len(arg) >= 1 else "load.json"
                NameSpace = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else defualt_NAME
                Value = json.dumps({"replace": False,"values": self.get_value(arg[2],func,**kwargs)}, indent=2,ensure_ascii=False) if len(arg) >= 3 else json.dumps({"replace": False,"values": []}, indent=2,ensure_ascii=False)
                path = defualt_DataPath+NameSpace +'\\tags\\' + self.get_value(arg[3],func,**kwargs) if len(arg) >= 4 else defualt_DataPath+NameSpace +'\\tags\\'
                self.WriteT(Value,Tagsname,path)
                return [True,int]
            elif(func_name == 'checkBlock'):
                Pos = str(self.get_value(arg[0],func,**kwargs)) if len(arg) >= 1 else "0 0 0"
                Id = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else "air"
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].return','append',{"value":0},func,**kwargs)
                self.write_file(func,f"execute store success storage {defualt_STORAGE} main_tree[-1].return[-1].value double 1.0 if block {Pos} {Id}\n",**kwargs)
                return [1,float]
            elif(func_name == 'rebuild'):
                ...
        else:
            ## mc 类处理
            if attribute_name == "MC.ENTITY":
                if(func_name == 'get_data'):
                    value = self.get_value(arg[0],func,**kwargs) if len(arg) >= 1 else "UUID"
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].return','append',{"value":0},func,**kwargs)
                    self.write_file(func,f"data modify storage {defualt_STORAGE} main_tree[-1].return[-1].value set from entity {self.py_get_value(var)} {value}\n",**kwargs)

        return [None,None]


# 用户自定义类的调用
class ClassCall(Parser):
    '''自定义类 处理器'''
    def __init__(self,main_tree,class_name=None,*args,**kwargs) -> None:
        self.main_tree = main_tree
        self.class_name = class_name
    def init(self,func,*args,**kwargs) -> bool:
        '''自定义类的实例化处理'''
        for item in self.main_tree[0]["class_list"]:
            if item['id'] == self.class_name:
                self.write_file(func,f'#类方法调用.参数处理\n',**kwargs)
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"self"}}].value set value []\n',**kwargs)
                for item2 in item['functions']:
                    if item2['id'] == "__init__":
                        shift = 0
                        for i in range(len(item2['args'])):
                            id = item2['args'][i]
                            if id != 'self':
                                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{id}"}}].value set from storage {defualt_STORAGE} main_tree[-1].call_list[-1][{i-shift}].value\n',**kwargs)
                            else:
                                shift +=1
                        self.write_file(func,f'#类方法调用.初始化\n',**kwargs)
                        self.write_file(func,f"function {defualt_NAME}:{item['id']}/{item2['id']}/_start\n",**kwargs)
                        break
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":"self"}}].value\n',**kwargs)
                return [[],self.class_name]
        return [None,None]
    def main(self,var_name,class_name,call_name,IsCallFunc,func,storage,*args,**kwargs) -> bool:
        # print(var_name,class_name,call_name,IsCallFunc)
        '''属性调用
        var_name 变量名称 class_name 类名称 call_name 调用的名称 IsCallFunc 是否为调用函数
        '''
        if var_name == "self":
            class_name = kwargs["ClassName"]
        
        if IsCallFunc:
            for item in self.main_tree[0]["class_list"]:
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
                                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{id}"}}].value set from storage {defualt_STORAGE} main_tree[-1].call_list[-1][{i-shift}].value\n',**kwargs)
                                else:
                                    if var_name != None:
                                        # 如果有指定的 var_name
                                        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"self"}}].value set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{var_name}"}}].value\n',**kwargs)
                                        # 如果没有则可能为方法调用方法
                                    else:
                                        if storage == None:
                                            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"self"}}].value set from storage {defualt_STORAGE} main_tree[-1].return[-1].value\n',**kwargs)
                                        else:
                                            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"self"}}].value set from {storage}\n',**kwargs)
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
                                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{var_name}"}}].value set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":"self"}}].value\n',**kwargs)
                                elif storage != None:
                                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {storage} set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":"self"}}].value\n',**kwargs)
                            return [[],item2['type']]
        else:
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{var_name}"}}][{{"id":"{call_name}"}}].value\n',**kwargs)
        #无
        return [None,None]

    def class_var_to_str(self,tree:ast.Attribute,func,**kwargs):
        '''将实例化对象调用的值转 字符串
        
        - 主要用于 赋值中的类处理
        - 例如：

        >>> self.a.x = 1
        '''
        if isinstance(tree.value,ast.Attribute):
            return self.class_var_to_str(tree.value,func,**kwargs) + f'[{{"id":"{tree.attr}"}}].value'
        elif isinstance(tree.value,ast.Name):
            return f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.value.id}"}}].value[{{"id":"{tree.attr}"}}].value'
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
                if j['id'] == tree.attr:
                    return j
            x["value"].append({"id":tree.attr,"value":[],"type":None})
            return x["value"][-1]

        elif isinstance(tree.value,ast.Name):
            for i in self.main_tree[-1]['data']:
                if i['id'] == tree.value.id:
                    for j in i['value']:
                        if j['id'] == tree.attr:
                            return j
                    i['value'].append({"id":tree.attr,"value":[]})
                    return i['value'][-1]
            self.main_tree[-1]['data'].append({"id":tree.value.id,"value":[{"id":tree.attr,"value":[],"type":None}],"type":None})
            return self.main_tree[-1]['data'][-1]['value'][-1]



# 类型的属性调用 + py内置方法与属性
class TypeAttributeHandler(Parser):
    '''根据类型处理 属性'''
    def __init__(self,tree,value ,Type,attr:str,name:str,IsCallFunc:int, *args, **kwargs):
        self.main_tree = tree
        self.Value = value
        self.type = Type
        self.name = name
        self.IsCallFunc = IsCallFunc
        self.attr = attr
        self.storage = kwargs.get("storage")
        if self.storage == None:
            self.storage = f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{self.name}"}}].value'
    def get_value(self,arg,func=None,*args,**kwargs):
        if isinstance(arg,ast.Constant):
            return arg.value
        elif isinstance(arg,ast.Name):
            return self.py_get_value(arg.id,**kwargs)
        elif isinstance(arg,ast.List):
            self.main_tree[-1]["list_handler"] = []
            for item in arg.elts:
                self.main_tree[-1]["list_handler"].append(self.get_value(item))
            return self.main_tree[-1]["list_handler"]
    def main(self,func,**kwargs):
        # 类型:
        #       变量,
        #       函数
        
        # 系统内置类
        if self.type == "str":
            if not self.IsCallFunc:
                if self.attr == "hash":
                    return [self.Value.__hash__(),"int"]
            else:
                if self.attr == "replace":
                    return [self.Value.replace(self.get_value(self.main_tree[-1]["call_list"][0]),self.get_value(self.main_tree[-1]["call_list"][1])),"str"]
        if self.type == "list":
            if not self.IsCallFunc:
                if self.attr == "hash":
                    return [self.Value.__hash__(),"int"]
            else:
                if self.attr == "append":
                    self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {self.storage} append from storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value\n',**kwargs)
                    return [self.Value.append(self.get_value(self.main_tree[-1]["call_list"][0])),"list"]
                elif self.attr == "pop":
                    #动态命令
                    self.mcf_build_dynamic_command([f'storage {defualt_STORAGE} main_tree[-1].call_list[-1][-1].value'],[f'$data remove {self.storage}[$(arg0)]'],func,**kwargs)
                    index = self.get_value(self.main_tree[-1]["call_list"][0])
                    if not isinstance(index,int):
                        index = 0
                        if self.Value:
                            return [self.Value.pop(0),"list"]
                    try:
                        return [self.Value.pop(index),"list"]
                    except:
                        if self.Value:
                            return [self.Value.pop(0),"list"]
                        return [self.Value,"list"]
        # 自定义的类
        else:
            # if not self.IsCallFunc:
            
            ClassC = ClassCall(self.main_tree,self.type,**kwargs)
            x:list=ClassC.main(self.name,self.type,self.attr,self.IsCallFunc,func,self.storage,**kwargs)
            if self.IsCallFunc:
                x.append({"haveCallFunc":True})
            return x
            # else:
            #     self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{self.name}"}}][{{"id":"{self.attr}"}}].value\n',**kwargs)
            #     return [None,None]
        return [None,None]

# 运算符重载 TODO
class OperatorOverloadingHandler(Parser):
    '''根据类型处理 运算符重载'''
    def __init__(self, tree,content,attr:str,IsCallFunc:int, *args, **kwargs):
        self.main_tree = tree
        self.type = content
        self.IsCallFunc = IsCallFunc
        self.attr = attr
    def get_value(self,arg,func=None,*args,**kwargs):
        if isinstance(arg,ast.Constant):
            return arg.value
        elif isinstance(arg,ast.Name):
            return self.py_get_value(arg.id,**kwargs)
        elif isinstance(arg,ast.List):
            self.main_tree[-1]["list_handler"] = []
            for item in arg.elts:
                self.main_tree[-1]["list_handler"].append(self.get_value(item))
            return self.main_tree[-1]["list_handler"]
    def main(self,func,**kwargs):
        if self.type == "str":
            if not self.IsCallFunc:
                if self.attr == "x":
                    ...
            else:
                if self.attr == "relpace":
                    return [""]

# 装饰器处理器
class DecoratoHandler(Parser):
    def __init__(self,main_tree):
        self.main_tree = main_tree
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
            events.main(decorator,self.main_tree[0]["eventCounter"],callFunctionName,**kwargs)
        if self.check(decorator) == 3:
            events = ExecHandler(self.main_tree)
            self.main_tree = events.main(decorator,callFunctionName,**kwargs)
        if self.check(decorator) == 4:
            events = CacheHandler(self.main_tree)
            self.main_tree = events.main(decorator,callFunctionName,**kwargs)
        if self.check(decorator) == 5:
            events = FunctionTagHandler(self.main_tree)
            self.main_tree = events.main(decorator,callFunctionName,**kwargs)
        return self.main_tree

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
    def __init__(self,main_tree):
        self.main_tree = main_tree
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
        return self.main_tree

# 函数标签处理器
class FunctionTagHandler(DecoratoHandler):
    def __init__(self,main_tree):
        self.main_tree = main_tree
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
        return self.main_tree

# 函数缓存处理器
class CacheHandler(DecoratoHandler):
    def __init__(self,main_tree):
        self.main_tree = main_tree
    def main(self,decorator,callFunctionName,*args, **kwargs):
        x = self.get_func_info(kwargs.get("ClassName") if kwargs.get("ClassName") else "",callFunctionName,**kwargs)
        x['cached'] = True
        self.write_file(callFunctionName,f"##缓存函数-判断缓存数据\n    #先字符串化参数\n",**kwargs)
        # 参数转字符串
            #动态命令
        # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].dync','set',{},callFunctionName,**kwargs)
        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].dync.arg0','set',f'storage {defualt_STORAGE} main_tree[-1].call_list[-1]',callFunctionName,**kwargs)
        self.mcf_call_function(f'{callFunctionName}/dync_{self.main_tree[0]["dync"]}/_start with storage {defualt_STORAGE} main_tree[-1].dync',callFunctionName,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        
        self.write_file(callFunctionName,f"    #字符串的参数作为键，索引结果\n",**kwargs)
        self.write_file(callFunctionName,f"execute if score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run return 1\n",**kwargs)
        self.mcf_call_function(f'{callFunctionName}/dync_{self.main_tree[0]["dync"]+1}/_start with storage {defualt_STORAGE} main_tree[-1].dync',callFunctionName,False,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run ',**kwargs)
        # 内容
        kwargs['p'] = f'{callFunctionName}//dync_{self.main_tree[0]["dync"]}//'
        kwargs['f2'] = f'_start'

        self.write_file(callFunctionName,f'##    动态命令\n$data modify storage {defualt_STORAGE} main_tree[-1].dync.arg0 set value \'$(arg0)\'\n$data modify storage {defualt_STORAGE} main_tree[-1].key set value \'$(arg0)\'\n',inNewFile=True,**kwargs)
        self.main_tree[0]["dync"] += 1
        # 字符串的参数作为键，索引结果
        # 内容
        kwargs['p'] = f'{callFunctionName}//dync_{self.main_tree[0]["dync"]}//'
        CachedData = f'storage {defualt_STORAGE} main_tree[0].CachedFunctions[{{"id":"{callFunctionName}"}}].\'$(arg0)\''
        if kwargs.get("ClassName"):
            CachedData = f'storage {defualt_STORAGE} main_tree[0].CachedMethod[{{"id":"{kwargs.get("ClassName")}"}}].value[{{"id":"{callFunctionName}"}}].\'$(arg0)\''
        self.write_file(callFunctionName,f'##    动态命令\n$execute if data {CachedData} run scoreboard players set #{defualt_STORAGE}.stack.end {scoreboard_objective} 1\n$execute if data {CachedData} run data modify storage {defualt_STORAGE} main_tree[-2].return append from {CachedData}\n',inNewFile=True,**kwargs)
        self.main_tree[0]["dync"] += 1


        # self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].dync','set',{},callFunctionName,**kwargs)
        return self.main_tree





