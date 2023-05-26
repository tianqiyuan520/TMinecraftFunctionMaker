import copy
import json
import re
import ast
import os
from read_config import read_json
from model.mcf_storage_editor import Storage_editor
from model.mc_nbt import MCStorage,RawJsonText

from config import defualt_PATH #默认路径
from config import defualt_STORAGE # STORAGE
from config import scoreboard_objective # 默认记分板
from config import defualt_NAME # 项目名称
from config import system_functions # 内置 函数调用表
from config import custom_functions # 自定义 函数调用表

class Parser(Storage_editor):
    '''解析程序'''
    def __init__(self,content,*args,**kwargs) -> None:
        self.code = content
        # 模拟栈 [{  "data":[{"id":"x","value":"","is_global":False},{...}],"is_end":0,"is_return":0,"is_break":0,"is_continue":0,"return":[{"id":"x","value":""}],"type":""  },"exp_operation":[{"value":""}],"functions":[{"id":"","args":[],"call":"","BoolOpTime":0,"Subscript":[{"value":""}]}]]
        # data为记录数据,is_return控制当前函数是否返回,is_end控制该函数是否终止,is_break控制循环是否终止,is_continue是否跳过后续的指令,return 记录调用的函数的返回值 , exp_operation 表达式运算的过程值(栈) is_global 判断该变量是否为全局变量 functions记录函数参数列表,函数调用接口,当前函数 BoolOpTime 条件判断 累计次数 Subscript为记录切片结果 condition_time记录该函数逻辑运算时深度遍历的编号（属于临时变量） "boolOPS"记录逻辑运算的结果 boolResult 记录实际逻辑运算结果（用于判断and or）elif_time 记录 elif次数(临时数据) while_time记录 while次数 for_time 记录 for 次数 for_list 记录for迭代的列表([{"value":xx},{..},...]) "call_list" 调用函数的参数列表(  [{"value":"","id":"",is_constant:True}   ]   ,若有id则为kwarg ) 
        #  类型:  BinOp Constant Name BoolOp Compare UnaryOp Subscript list tuple Call Attribute
        self.main_tree:list[dict] = [{"data":[],"is_break":0,"is_continue":0,"return":[],"type":"","is_return":0,"is_end":0,"exp_operation":[],"functions":[],"BoolOpTime":0,"condition_time":0,"elif_time":0,"while_time":0,"for_time":0,"call_list":[]}]
        #初始化计分板
        self.write_file('load',f'scoreboard objectives add {scoreboard_objective} dummy\n',**kwargs)
        # self.write_file('load',f'scoreboard players reset * {scoreboard_objective}\n',**kwargs)
        self.write_file('load',f'#初始化栈\n',**kwargs)
        self.write_file('load',f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree set value [{{"data":[],"return":[],"type":"","exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[]}}]\n',**kwargs)
        self.parse('load',**kwargs)
    def parse(self,func:str,*args,**kwargs):
        '''func为当前函数的名称'''
        code = copy.deepcopy(self.code)
        code_ = ast.parse(code)
        print(ast.dump(code_))
        #遍历python的ast树
        self.walk(code_.body,func,-1,**kwargs)
        print(self.main_tree)
    def walk(self,tree:list,func:str,index:-1,*args,**kwargs):
        '''遍历AST'''
        kwargs_ = copy.deepcopy(kwargs)
        for item in tree:
            # 如果是赋值
            if isinstance(item,ast.Assign):
                self.Assign(item,func,index,**kwargs)
            # 全局化
            elif isinstance(item,ast.Global):
                self.Global(item,func,index,**kwargs)
            # 赋值+= -= *= /=
            elif isinstance(item,ast.AugAssign):
                self.AugAssign(item,func,index,**kwargs)
            # 函数定义
            elif isinstance(item,ast.FunctionDef):
                self.FunctionDef(item,item.name,index,**kwargs)
            # 函数调用
            elif isinstance(item,ast.Expr):
                self.Expr(item,func,index,**kwargs)
            # 函数返回
            elif isinstance(item,ast.Return):
                self.Return(item,func,**kwargs)
            # 逻辑运算
            elif isinstance(item,ast.If):
                self.main_tree[-1]['condition_time'] = 0
                self.main_tree[-1]['elif_time'] = 0
                self.main_tree[-1]['BoolOpTime'] += 1
                self.write_file(func,f'scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                self.If(item,self.main_tree[-1]['condition_time'],func,True,**kwargs)
            # while 循环
            elif isinstance(item,ast.While):
                self.main_tree[-1]['BoolOpTime'] += 1
                self.While(item,func,**kwargs)
            # For 循环 
            elif isinstance(item,ast.For):
                self.main_tree[-1]['BoolOpTime'] += 1
                self.For(item,func,**kwargs)
            # Break 
            elif isinstance(item,ast.Break):
                self.Break(item,func,**kwargs)
            # Continue 
            elif isinstance(item,ast.Continue):
                self.Continue(item,func,**kwargs)
            kwargs = kwargs_
    def write_file(self,func:str,text,*args,**kwargs):
        '''写文件 f2为函数详细名称,p为函数的相对位置'''
        func2 = '_start'
        PATH_ = None
        Is_def_func = False
        for key, value in kwargs.items():
            if((key=='f2'or key ==  'func2') and value != None):
                func2 = value
            if(key=='p'or key ==  'path'):
                PATH_ = value
            if(key=='def_function' and value == True):
                Is_def_func = True
        if(Is_def_func):
            PATH_ = None
        if(PATH_==None):
            path = defualt_PATH+'functions\\'+func+'\\'
            func_path = defualt_PATH+'functions\\'+func+'\\'+func2+'.mcfunction'
            folder = os.path.exists(path)
            if not folder:
                os.makedirs(path)
            folder = os.path.exists(func_path)
            if folder:
                with open(func_path,'a',encoding='utf-8') as f:
                    f.write(text)
            else:
                with open(func_path,'w',encoding='utf-8') as f:
                    f.write(text)
        else:
            PATH_ = defualt_PATH+'functions\\'+PATH_+'\\'
            func_path = PATH_+func2+'.mcfunction'
            folder = os.path.exists(PATH_)
            if not folder:
                os.makedirs(PATH_)
            folder = os.path.exists(func_path)
            if folder:
                with open(func_path,'a',encoding='utf-8') as f:
                    f.write(text)
            else:
                with open(func_path,'w',encoding='utf-8') as f:
                    f.write(text)
        return self

    def py_append_tree(self):
        '''新建堆栈值'''
        self.main_tree.append({"data":[],"is_break":0,"is_continue":0,"return":[],"type":"","is_return":0,"is_end":0,"exp_operation":[],"functions":[],"BoolOpTime":0,"condition_time":0,"elif_time":0,"while_time":0,"for_time":0,"call_list":[]})
        return self

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
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree[{index}].exp_operation insert -1 from storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{i.id}"}}].value\n',**kwargs)
                self.mcf_change_exp_operation(tree.op,func,index)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value\n',**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            i =tree.target
            if isinstance(i,ast.Name):
                value = tree.value.value
                self.py_change_value(i.id,value,True,func,False,index,**kwargs)
                self.mcf_change_value_by_operation(i.id,value,self.py_get_value_global(i.id,func,-1),tree.op,func,index,**kwargs)
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
                self.mcf_change_value_by_operation2(f'{defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value',f'{defualt_STORAGE} main_tree[-1].Subscript.value',tree.op,func,-1,**kwargs)
                if(is_global):
                    self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value',f'#{defualt_NAME}.system.temp1 {scoreboard_objective}','double',0.001,func,**kwargs)
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
                    self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value',f'#{defualt_NAME}.system.temp1 {scoreboard_objective}','double',0.001,func,**kwargs)

    def Global(self,tree:ast.Global,func:str,index:-1,*args,**kwargs):
        '''Global 全局变量 '''
        for i in tree.names:
            for j in self.main_tree[0]["data"]:
                if j["id"] == i:
                    self.main_tree[index]["data"].append({"id":i,"value":j["value"],"is_global":True})
                    self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{j["id"]}"}}].value set from storage {defualt_STORAGE} main_tree[0].data[{{"id":{j["id"]}}}].value\n',**kwargs)

    def BinOp(self,tree:ast.BinOp,op:ast.operator,func:str,index:-1,index2:-1,*args,**kwargs) -> ast.Constant:
        '''运算操作
        tree新的树，op操作类型 +-*/
        '''
        # 类型扩建TODO
        ##判断左右值
        if isinstance(tree.left,ast.BinOp):
            tree.left = self.BinOp(tree.left,tree.left.op,func,index,index2,**kwargs)
            if isinstance(tree.left,ast.Constant) and (tree.left.kind == "have_operation"):
                self.mcf_add_exp_operation(tree.left.value,func,index,**kwargs)
        if isinstance(tree.right,ast.BinOp):
            tree.right = self.BinOp(tree.right,tree.right.op,func,index,index2,**kwargs)
            if isinstance(tree.right,ast.Constant) and (tree.right.kind == "have_operation"):
                self.mcf_add_exp_operation(tree.right.value,func,index,**kwargs)
        tree_list:ast = [tree.left,tree.right]
        for item in range(2):
            # 假如为变量
            if isinstance(tree_list[item],ast.Name):
                value = self.py_get_value(tree_list[item].id,func,index,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree_list[item].id}"}}].value',func,**kwargs)
                tree_list[item] = ast.Constant(value=value, kind="is_v")
            # 假如为函数返回值
            elif isinstance(tree_list[item],ast.Call):
                # 函数返回值 赋值
                self.Expr(ast.Expr(value=tree_list[item]),func,-1,*args,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
                value = 0
                tree_list[item] = ast.Constant(value=value, kind="is_call")
            elif isinstance(tree_list[item],ast.Subscript):
                # 切片赋值
                self.Subscript(tree_list[item],func,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].exp_operation','append',{"value":0,"type":"num"},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript.value',func,**kwargs)
                value = 0
                tree_list[item] = ast.Constant(value=value, kind="is_call")
        tree.left,tree.right = (tree_list[0],tree_list[1])
        # 常量处理
        if isinstance(tree.left,ast.Constant) and isinstance(tree.right,ast.Constant):
            ##mcf 处理
            if (tree.left.kind == None) and (tree.right.kind == None):
                value = self.get_operation(tree.left.value,tree.right.value,op,func,**kwargs)
                return ast.Constant(value=value, kind="have_operation")
            else:
                value = None
                #受变量影响的值
                if (tree.left.kind == None):
                    self.mcf_add_exp_operation(tree.left.value,func,index,**kwargs)
                if (tree.right.kind == None):
                    self.mcf_add_exp_operation(tree.right.value,func,index,**kwargs)
                self.mcf_change_exp_operation(op,func,index,**kwargs)
                return ast.Constant(value=value, kind='is_v')

    def get_operation(self,num1,num2,operation,func,*args,**kwargs):
        '''运算 返回结果'''
        # self.mcf_change_exp_operation(operation,func)
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

    def Assign(self,tree:ast.Assign,func:str,index:-1,*args,**kwargs):
        '''赋值操作'''
        # 类型扩建TODO
        if isinstance(tree.value,ast.BinOp):
            tree.value = self.BinOp(tree.value,tree.value.op,func,index,index,**kwargs)
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,tree.value.value,False,func,False,index,**kwargs)
                    if (tree.value.kind == None):
                        self.mcf_add_exp_operation(tree.value.value,func,index)
                    self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value\n',**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,tree.value.value,True,func,False,index,**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value2(i.id,tree.value.id,func,False,index,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            # 切片赋值
            self.Subscript(tree.value,func,**kwargs)
            value = 0
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    if(is_global):
                        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[-1].Subscript.value\n',**kwargs)
                    self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value set from storage {defualt_STORAGE} main_tree[-1].Subscript.value\n',**kwargs)
        elif isinstance(tree.value,ast.Call):
            # 函数返回值 赋值
            self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # python 赋值 主要是查是否为全局变量
            value = 0
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_change_value(i.id,value,False,func,False,index,**kwargs)
                    is_global = self.py_get_value_global(i.id,func,index,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
        elif isinstance(tree.value,ast.BoolOp):
            # 函数返回值 赋值
            self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # python 赋值 主要是查是否为全局变量
            value = 0
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    #
                    self.BoolOP_call(tree.value,func,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":0}}][-1]',func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{i.id}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-2].boolResult[{{"id":0}}][-1]',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Compare):
            # 函数返回值 赋值
            self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # python 赋值 主要是查是否为全局变量
            value = 0
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    #
                    self.Compare_call(tree.value,func,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value int 1',f'scoreboard players get #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-2].data[{{"id":"{i.id}"}}].value int 1',f'scoreboard players get #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.UnaryOp):
            # 函数返回值 赋值
            self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            # python 赋值 主要是查是否为全局变量
            value = 0
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    #
                    self.UnaryOp_call(tree.value,func,**kwargs)
                    # mcf 赋值
                    if is_global:
                        self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[0].data[{{"id":"{i.id}"}}].value int 1',f'scoreboard players get #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-2].data[{{"id":"{i.id}"}}].value int 1',f'scoreboard players get #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)

    def py_get_value(self,key,func:str,index:-1,*args,**kwargs):
        '''获取py记录的堆栈值 变量值'''
        for i in self.main_tree[index]["data"]:
            if i["id"] == key:
                return i["value"]
        #无
        for i in self.main_tree[0]["data"]:
            if i["id"] == key:
                return i["value"]
        return None

    def py_get_value_global(self,key,func:str,index:-1,*args,**kwargs) -> bool:
        '''获取py记录的堆栈值 变量是否为全局变量'''
        for i in self.main_tree[index]["data"]:
            if i["id"] == key:
                if i.get("is_global")!=None:
                    return i["is_global"]
        #无
        for i in self.main_tree[0]["data"]:
            if i["id"] == key:
                return True

    def py_change_value(self,key,value,call_mcf:True,func:str,isfundef:False,index:-1,*args,**kwargs):
        '''
        修改py记录的堆栈值
        常量修改
        isfundef 是否为函数的定义
        '''
        NO_exist = True
        is_global = False
        for i in self.main_tree[index]["data"]:
            if i["id"] == key:
                i["value"] = value
                NO_exist = False
                if(i.get("is_global")==True):
                    for j in self.main_tree[0]["data"]:
                        if j["id"] == key:
                            j["value"] = value
                            is_global = True
                else:
                    i["is_global"] = False
        if NO_exist:
            self.main_tree[index]["data"].append({"id":key,"value":value,"is_global":False})
        if(call_mcf):
            self.mcf_change_value(key,value,is_global,func,isfundef,index,**kwargs)
        return self

    def py_change_value2(self,key,key2,func:str,isfundef:False,index:-1,*args,**kwargs):
        '''
        修改py记录的堆栈值
        变量修改
        isfundef 是否为函数的定义
        '''
        value = self.py_get_value(key2,func,index)
        NO_exist = True
        is_global = False
        for i in self.main_tree[index]["data"]:
            if i["id"] == key:
                i["value"] = value
                NO_exist = False
                if(i["is_global"]):
                    for j in self.main_tree[0]["data"]:
                        if j["id"] == key:
                            j["value"] = value
                            is_global = True
        if NO_exist:
            self.main_tree[index]["data"].append({"id":key,"value":value})
        self.mcf_change_value2(key,key2,is_global,func,isfundef,index,index)

    def py_call_list_append(self,index:int,value:dict,*args,**kwargs):
        self.main_tree[index]["call_list"].append(value)


    def FunctionDef(self,tree:ast.FunctionDef,func:str,index:-1,*args,**kwargs):
        '''函数定义'''
        kwargs['def_function'] = True
        self.py_append_tree()
        self.main_tree[0]["functions"].append({"id":func,"args":[],"call":"_start"})
        #函数参数初始化
        self.write_file(func,f'##函数参数初始化\n',**kwargs)
        for item in tree.args.args:
            if isinstance(item,ast.arg):
                self.main_tree[0]["functions"][-1]["args"].append(item.arg)
                self.FunctionDef_args_init(item,func,index,**kwargs)
        self.write_file(func,f'##函数主体\n',**kwargs)
        
        self.walk(tree.body,func,index,**kwargs)
        self.write_file(func,f'##函数结尾\n',**kwargs)
        self.write_file(func,f'data remove storage {defualt_STORAGE} main_tree[-1]\n',**kwargs)
        self.main_tree.pop(-1)


    def FunctionDef_args_init(self,tree:ast.arg,func:str,index:-1,*args,**kwargs):
        '''函数定义中 参数预先值'''
        # 类型扩建TODO
        if isinstance(tree.annotation,ast.BinOp):
            tree.annotation = self.BinOp(tree.annotation,tree.annotation.op,func,index,index-1,**kwargs)
            i = tree.arg
            self.py_change_value(i,tree.annotation.value,False,func,False,index,**kwargs)
            if (tree.annotation.kind == None):
                self.mcf_add_exp_operation(tree.annotation.value,func,index)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute unless data storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{i}"}}] run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{i}"}}].value set from storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value\n',**kwargs)
        elif isinstance(tree.annotation,ast.Constant):
            # 常数赋值
            self.py_change_value(tree.arg,tree.annotation.value,True,func,True,index,**kwargs)
        elif isinstance(tree.annotation,ast.Name):
            # 变量赋值
            self.py_change_value2(tree.arg,tree.annotation.id,func,True,index,**kwargs)

    def get_function_args(self,key,*args,**kwargs) ->list:
        '''获取函数 参数列表'''
        for i in self.main_tree[0]["functions"]:
            if i["id"] == key:
                return i["args"]
        return []

    def get_function_call_name(self,key,*args,**kwargs) ->str:
        '''获取函数 调回接口函数名称'''
        for i in self.main_tree[0]["functions"]:
            if i["id"] == key:
                return i["call"]
        ##非玩家自定义，或还未定义的函数返回默认值
        return "_start"

    def check_function_exist(self,key,*args,**kwargs) ->str:
        '''判断函数是否存在（即是否已定义）\n用于内置函数判断'''
        for i in self.main_tree[0]["functions"]:
            if i["id"] == key:
                return True
        ##非玩家自定义，或还未定义的函数返回False
        return False

    def Expr(self,tree:ast.Expr,func:str,index:-1,*args,**kwargs):
        '''函数调用 处理'''
        func_name = '' #函数名称
        Call = tree.value
        if isinstance(Call , ast.Call):
            if isinstance(Call.func , ast.Name):
                func_name = Call.func.id
                #函数参数赋值
                args = self.get_function_args(func_name,**kwargs)
                call_name = self.get_function_call_name(func_name,**kwargs)
                self.write_file(func,f'##函数调用_begin\n',**kwargs)
                self.write_file(func,f'#参数处理.函数处理\n',**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','set',[],func,**kwargs)
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
                if self.check_function_exist(func_name,**kwargs):
                    ## mcf
                    self.write_file(func,f'#参数处理.赋值\n',**kwargs)
                    #位置传参
                    for i in range(len(args)):
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{args[i]}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].call_list[{i}].value',func,**kwargs)
                    #关键字传参
                    for i in range(len(Call.keywords)):
                        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{Call.keywords[i].arg}"}}].value','set',f'storage {defualt_STORAGE} main_tree[-1].call_list[{{"id":{Call.keywords[i].arg}}}].value',func,**kwargs)
                    self.write_file(func,f'#函数调用\n',**kwargs)
                    self.write_file(func,f'function {defualt_NAME}:{func_name}/{call_name}\n',**kwargs)
                    self.write_file(func,f'##函数调用_end\n',**kwargs)
                else:
                    SF = System_function(self.main_tree,func_name,func,**kwargs)
                    SF.main(**kwargs)
            elif isinstance(Call.func , ast.Attribute):
                attribute_name = None
                if isinstance(Call.func.value,ast.Name):
                    attribute_name = Call.func.value.id
                func_name = Call.func.attr
                #函数参数赋值
                args = self.get_function_args(func_name,**kwargs)
                call_name = self.get_function_call_name(func_name,**kwargs)
                if(attribute_name!='mc'):
                    self.write_file(func,f'##函数调用_begin\n',**kwargs)
                    self.write_file(func,f'#参数处理.函数处理\n',**kwargs)
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','set',[],func,**kwargs)
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
                    SF = Custom_function(self.main_tree,attribute_name,func_name,**kwargs)
                    SF.main(func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
                else:
                    self.main_tree[-1]["call_list"] = Call.args
                    MCF =  mc_function(self.main_tree)
                    MCF.main(func_name,self.main_tree[-1]["call_list"],func,**kwargs)
        elif isinstance(Call , ast.Attribute):
            #属性 (类)
            ...

    def Expr_set_value(self,tree:ast.Assign,func,*args,**kwargs):
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
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1].value','set',f'storage {defualt_STORAGE} main_tree[{-1}].exp_operation[-1].value',func,**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_call_list_append(-1,{"value":tree.value.value,"id":i.id,"is_constant":True})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','append',{"value":tree.value.value,"id":f"{i.id}"},func,**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.py_call_list_append(-1,{"value":self.py_get_value(tree.value.id,func,False,-1,**kwargs),"id":i.id,"is_constant":False},**kwargs)
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.value.id}"}}].value',func,**kwargs)
        elif isinstance(tree.value,ast.BoolOp):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    #
                    self.main_tree[-1]['condition_time'] += 1
                    self.mcf_new_stack(func,**kwargs)
                    self.mcf_new_stack_inherit_data(func,**kwargs)
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    kwargs_ = copy.deepcopy(kwargs)
                    kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                    kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['def_function'] = False
                    self.BoolOp(tree.value,0,func,True,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                    self.BoolOp_operation(tree.value,0,0,func,**kwargs)
                    kwargs = kwargs_
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].call_list','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-2].call_list[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":0}}][-1]',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Compare):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.main_tree[-1]['condition_time'] += 1
                    self.mcf_new_stack(func,**kwargs)
                    self.mcf_new_stack_inherit_data(func,**kwargs)
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    self.Compare(tree.value,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                    self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].call_list','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-2].call_list[-1].value int 1',f'scoreboard players get #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.UnaryOp):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.mcf_new_stack(func,**kwargs)
                    self.mcf_new_stack_inherit_data(func,**kwargs)
                    self.main_tree[-1]['condition_time'] += 1
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    self.UnaryOp(tree.value,True,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                    self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].call_list','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-2].call_list[-1].value int 1',f'scoreboard players get #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
                    self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    self.Subscript(tree.value,func,**kwargs)
                    #
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript.value',func,**kwargs)
        elif isinstance(tree.value,ast.Call):
            for i in tree.targets:
                if isinstance(i,ast.Name):
                    # 函数返回值 赋值
                    self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
                    self.py_call_list_append(-1,{"value":0,"id":i.id,"is_constant":False})
                    self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].call_list','append',{"value":0,"id":f"{i.id}"},func,**kwargs)
                    self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].call_list[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].return.value',func,**kwargs)

    def Return(self,tree:ast.Return,func,*args,**kwargs):
        '''函数返回值处理'''
        # 类型扩建TODO
        self.write_file(func,f'##函数返回值处理_bengin\n',**kwargs)
        if isinstance(tree.value,ast.BinOp):
            tree.value = self.BinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(tree.value.value)
            if (tree.value.kind == None):
                self.mcf_add_exp_operation(tree.value.value,func,-1,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set from storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_return set value 1b\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_end set value 1b\n',**kwargs)
        elif isinstance(tree.value,ast.Constant):
            # 常数赋值
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(tree.value.value)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":{tree.value.value}}}\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_return set value 1b\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_end set value 1b\n',**kwargs)
        elif isinstance(tree.value,ast.Name):
            # 变量赋值
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(self.py_get_value(tree.value.id,func,-1))
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage {defualt_STORAGE} main_tree[-2].return append value {{"value":0}}\ndata modify storage {defualt_STORAGE} main_tree[-2].return[-1].value set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.value.id}"}}].value\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_return set value 1b\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_end set value 1b\n',**kwargs)
        elif isinstance(tree.value,ast.BoolOp):
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_new_stack(func,**kwargs)
            self.mcf_new_stack_inherit_data(func,**kwargs)
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            kwargs_ = copy.deepcopy(kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['def_function'] = False
            self.BoolOp(tree.value,0,func,True,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
            self.BoolOp_operation(tree.value,0,0,func,**kwargs)
            kwargs = kwargs_
            #
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-3].return','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-3].return[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":0}}][-1]',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(0)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_return set value 1b\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_end set value 1b\n',**kwargs)
        elif isinstance(tree.value,ast.Compare):
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_new_stack(func,**kwargs)
            self.mcf_new_stack_inherit_data(func,**kwargs)
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            self.Compare(tree.value,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            #
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-3].return[-1].value','append',{"value":0},func,**kwargs)
            self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-3].return[-1].value[-1].value int 1',f'scoreboard players get #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.UnaryOp):
            self.mcf_new_stack(func,**kwargs)
            self.mcf_new_stack_inherit_data(func,**kwargs)
            self.main_tree[-1]['condition_time'] += 1
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            self.UnaryOp(tree.value,True,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
            #
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-3].return[-1]','append',{"value":0},func,**kwargs)
            self.mcf_store_value_by_run_command(f'storage {defualt_STORAGE} main_tree[-3].return[-1][-1].value int 1',f'scoreboard players get #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
            self.mcf_remove_stack_data(func,**kwargs)
        elif isinstance(tree.value,ast.Subscript):
            if len(self.main_tree) >=2:
                self.main_tree[-2]['return'].append(0)
            self.Subscript(tree.value,func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-2].return[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript.value',func,**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_return set value 1b\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_end set value 1b\n',**kwargs)
        self.write_file(func,f'##函数返回值处理_end\n',**kwargs)

    def Subscript(self,tree:ast.Subscript,func,*args,**kwargs):
        '''切片处理'''
        # 类型扩建TODO
        if isinstance(tree.value,ast.Subscript):
            self.Subscript(tree.value,func,**kwargs)
            self.Subscript_index(tree.slice,func,**kwargs)
            self.write_file(func,f'data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].Subscript.value\n',**kwargs)
            self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/loop\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
            self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript.value set from storage t_algorithm_lib:array get_element_by_index.list2\n',**kwargs)
        else:
            if isinstance(tree.value,ast.Call):
                # 函数返回值
                self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
                self.Subscript_index(tree.slice,func,**kwargs)
                self.write_file(func,f'data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].return[-1].value\n',**kwargs)
                self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/loop\n',**kwargs)
                self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
                self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript.value set from storage t_algorithm_lib:array get_element_by_index.list2\n',**kwargs)
            elif isinstance(tree.value,ast.Name):
                # 变量
                self.Subscript_index(tree.slice,func,**kwargs)
                self.write_file(func,f'data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":{tree.value.id}}}].value\n',**kwargs)
                self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/loop\n',**kwargs)
                self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
                self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript.value set from storage t_algorithm_lib:array get_element_by_index.list2\n',**kwargs)
            elif isinstance(tree.value,ast.BinOp):
                # 运算
                self.Subscript_index(tree.slice,func,**kwargs)
                tree.value = self.BinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
                if (tree.value.kind == None):
                    self.mcf_add_exp_operation(tree.value.value,func,-1)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value\n',**kwargs)
                self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/loop\n',**kwargs)
                self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
                self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript.value set from storage t_algorithm_lib:array get_element_by_index.list2\n',**kwargs)
            elif isinstance(tree.value,ast.Constant):
                self.Subscript_index(tree.slice,func,**kwargs)
                self.write_file(func,f'data modify storage t_algorithm_lib:array get_element_by_index.list set from storage {defualt_STORAGE} main_tree[-1].data[{{"id":{tree.value.value}}}].value\n',**kwargs)
                self.write_file(func,f'function t_algorithm_lib:array/get_element_by_index/loop\n',**kwargs)
                self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript append value {{"value":0}}\n',**kwargs)
                self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].Subscript.value set from storage t_algorithm_lib:array get_element_by_index.list2\n',**kwargs)

    def Subscript_index(self,tree:ast.Index,func,*args,**kwargs):
        # 类型扩建TODO
        if isinstance(tree.value,ast.Subscript):
            self.Subscript(tree.value,func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #tal.array.get_element_by_index.index {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].Subscript.value\n',**kwargs)
        elif isinstance(tree.value,ast.Name):
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #tal.array.get_element_by_index.index {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].data[{{"id":{tree.value.id}}}].value\n',**kwargs)
        elif isinstance(tree.value,ast.Call):
            self.Expr(ast.Expr(value=tree.value),func,-1,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #tal.array.get_element_by_index.index {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].return[-1].value\n',**kwargs)
        elif isinstance(tree.value,ast.BinOp):
            tree.value = self.BinOp(tree.value,tree.value.op,func,-1,-1,**kwargs)
            if (tree.value.kind == None):
                self.mcf_add_exp_operation(tree.value.value,func,-1,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #tal.array.get_element_by_index.index {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value\n',**kwargs)
        elif isinstance(tree.value,ast.Constant):
            self.write_file(func,f'scoreboard players set #tal.array.get_element_by_index.index {scoreboard_objective} {tree.value.value}\n',**kwargs)

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
        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolResult','set',[],func,**kwargs)
        if mode:
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 run function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/call\n',**kwargs)
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
        else:
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 run function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/call\n',**kwargs)
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
        kwargs['f2'] = f'call'
        kwargs['def_function'] = False
        self.write_file(func,f'#\n',**kwargs)
        # 类型扩建TODO
        if isinstance(tree.test,ast.BoolOp):
            self.main_tree[-1]['condition_time'] += 1
            if mode:
                self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                kwargs['def_function'] = False
                self.BoolOp(tree.test,condition_time+1,func,mode,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.BoolOp_operation(tree.test,0,0,func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}][-1]\n',**kwargs)
            else:
                self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)

                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                kwargs['def_function'] = False
                
                self.BoolOp(tree.test,condition_time+1,func,False,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.BoolOp_operation(tree.test,0,0,func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}][-1]\n',**kwargs)
        if isinstance(tree.test,ast.BinOp):
            self.main_tree[-1]['condition_time'] += 1
            if mode:
                self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                kwargs['def_function'] = False
                self.BinOp(tree.test,tree.test.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            else:
                self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                kwargs['def_function'] = False
                self.BinOp(tree.test,tree.test.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Compare):
            self.main_tree[-1]['condition_time'] += 1
            if mode:
                self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                self.Compare(tree.test,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            else:
                self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                self.Compare(tree.test,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
        elif isinstance(tree.test,ast.UnaryOp):
            self.main_tree[-1]['condition_time'] += 1
            if mode:
                self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                self.UnaryOp(tree.test,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
            else:
                self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                self.UnaryOp(tree.test,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
        elif isinstance(tree.test,ast.Name):
            self.main_tree[-1]['condition_time'] += 1

            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.test.id}"}}].value',func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Constant):
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":tree.test.value},func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Subscript):
            self.main_tree[-1]['condition_time'] += 1
            self.Subscript(tree.test,func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript.value',func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        #body
        kwargs = copy.deepcopy(kwargs_)
        self.write_file(func,f'#\n',**kwargs)
        if not only_test:
            if mode:
                #调用
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/main\n',**kwargs)
                kwargs['def_function'] = False
                self.walk(tree.body,func,-1,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'main')
            else:
                #调用
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/main\n',**kwargs)
                kwargs['def_function'] = False
                self.walk(tree.body,func,-1,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'main')
            if len(tree.orelse) >0:
                if isinstance(tree.orelse[0],ast.If) and len(tree.orelse) ==1:
                #elif
                    self.main_tree[-1]['elif_time'] += 1
                    self.main_tree[-1]['condition_time'] = 0
                    self.If(tree.orelse[0],0,func,False,**kwargs)
                else:
                    self.write_file(func,f'#\n',**kwargs)
                        #调用 else
                    self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 run function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/else/main\n',**kwargs)
                    # kwargs['def_function'] = False
                    self.walk(tree.orelse,func,-1,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//else//',f2=f'main')


    def BoolOp(self,tree:ast.BoolOp,condition_time:0,func:str,mode:bool = True,*args,**kwargs):
        '''逻辑运算 and or '''
        for item in tree.values:
            # 类型扩建TODO
            if isinstance(item,ast.BoolOp):
                self.main_tree[-1]['condition_time'] += 1
                if mode:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    self.BoolOp_operation(item,self.main_tree[-1]["condition_time"],condition_time,func,**kwargs)
                    self.BoolOp(item,self.main_tree[-1]["condition_time"],func,mode,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                else:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    self.BoolOp_operation(item,self.main_tree[-1]["condition_time"],condition_time,func,**kwargs)
                    self.BoolOp(item,condition_time,func,mode,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}')
            elif isinstance(item,ast.Compare):
                self.main_tree[-1]['condition_time'] += 1
                if mode:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
                    self.Compare(item,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                    
                else:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
                    self.Compare(item,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}')
            elif isinstance(item,ast.UnaryOp):
                self.main_tree[-1]['condition_time'] += 1
                if mode:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
                    self.UnaryOp(item,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                else:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
                    self.UnaryOp(item,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}')
            elif isinstance(item,ast.Name):
                self.main_tree[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                else:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{item.id}"}}].value',func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}][-1]\n',**kwargs)
                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
            elif isinstance(item,ast.Constant):
                self.main_tree[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                else:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":item.value},func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}][-1]\n',**kwargs)
                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
            elif isinstance(item,ast.BinOp):
                self.main_tree[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                else:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                
                self.BinOp(item,item.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
            elif isinstance(item,ast.Subscript):
                self.main_tree[-1]['condition_time'] += 1
                kwargs_ = copy.deepcopy(kwargs)
                if mode:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                else:
                    self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/elif_{self.main_tree[-1]["elif_time"]}/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
                    kwargs['p']=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                    kwargs['f2']=f'{self.main_tree[-1]["condition_time"]}'
                
                self.Subscript(item,func,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript.value',func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)

                kwargs = kwargs_
                self.BoolOp_record(tree,condition_time,self.main_tree[-1]["condition_time"],func,**kwargs)
    def Compare(self,tree:ast.Compare,condition_time:0,func:str,*args,**kwargs):
        '''判断语句 > < == != >= <='''
        #左
        # 类型扩建TODO
        if isinstance(tree.left,ast.BinOp):
            self.BinOp(tree.left,tree.left.op,func,-1,-1,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
        elif isinstance(tree.left,ast.Constant):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":tree.left.value},func,**kwargs)
        elif isinstance(tree.left,ast.Name):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.left.id}"}}].value',func,**kwargs)
        elif isinstance(tree.left,ast.Call):
            # 函数返回值 赋值
            self.Expr(ast.Expr(value=tree.left),func,-1,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
        #右
        # 类型扩建TODO
        for item in tree.comparators:
            if isinstance(item,ast.BinOp):
                self.BinOp(item,item.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
            elif isinstance(item,ast.Constant):
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":item.value},func,**kwargs)
            elif isinstance(item,ast.Name):
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.left.id}"}}].value',func,**kwargs)
            elif isinstance(item,ast.Call):
            # 函数返回值 赋值
                self.Expr(ast.Expr(value=item),func,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].return[-1].value',func,**kwargs)
        #再根据判断类型 > < >= <= != ==
        for item in tree.ops:
            if isinstance(item,ast.cmpop):
                self.mcf_reset_score(f'#{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}',func,**kwargs)
                self.mcf_compare_Svalues(f'{defualt_STORAGE} main_tree[-1].boolOPS[-2].value',f'{defualt_STORAGE} main_tree[-1].boolOPS[-1].value',item,func,f'scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} 1',**kwargs)

    def UnaryOp(self,tree:ast.UnaryOp,mode:bool,condition_time:0,func:str,*args,**kwargs):
        '''条件 取反语句 '''
        self.write_file(func,f'scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        # self.If(ast.If(test=tree.operand,body=[],orelse=[]),condition_time,func,mode,only_test=True,**kwargs)
        # 类型扩建TODO
        if isinstance(tree.operand,ast.BoolOp):
            if mode:
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                kwargs['def_function'] = False
                self.BoolOp(tree.operand,condition_time+1,func,mode,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.BoolOp_operation(tree.operand,0,0,func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}][-1]\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                kwargs['def_function'] = False
                
                self.BoolOp(tree.operand,condition_time+1,func,False,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.BoolOp_operation(tree.operand,0,0,func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}][-1]\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
        if isinstance(tree.operand,ast.BinOp):
            if mode:
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
                kwargs['def_function'] = False
                self.BinOp(tree.operand,tree.operand.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
                kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//'
                kwargs['def_function'] = False
                self.BinOp(tree.operand,tree.operand.op,func,-1,-1,**kwargs)
                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
                self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Compare):
            if mode:
                self.Compare(tree.operand,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                self.Compare(tree.operand,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}')
                self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
                #取反
                self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.UnaryOp):
            if mode:
                self.UnaryOp(tree.operand,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
                #取反
                self.get_condition_reverse(func,**kwargs)
            else:
                self.UnaryOp(tree.operand,mode,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//elif_{self.main_tree[-1]["elif_time"]}//',f2=f'{self.main_tree[-1]["condition_time"]}')
                #取反
                self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Name):

            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.operand.id}"}}].value',func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            #取反
            self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Constant):
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":tree.operand.value},func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            #取反
            self.get_condition_reverse(func,**kwargs)
        elif isinstance(tree.operand,ast.Subscript):
            self.Subscript(tree.operand,func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript.value',func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
            #取反
            self.get_condition_reverse(func,**kwargs)


    def BoolOp_operation(self,tree:ast.BoolOp,condition_time:int,condition_time2:int,func:str,*args,**kwargs):
        '''逻辑运算中 and or'''
        if isinstance(tree.op,ast.And):
            self.write_file(func,f'''
##和
execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count1 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}]
execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count2 {scoreboard_objective} run data modify storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}][] set value 0
execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run scoreboard players operation #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count1 {scoreboard_objective} -= #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count2 {scoreboard_objective}
execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count1 {scoreboard_objective} matches 1.. run data modify storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time2}}}].value append value 0
''',**kwargs)
        elif isinstance(tree.op,ast.Or):
            self.write_file(func,f'''
##或
execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count1 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}]
execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count2 {scoreboard_objective} run data modify storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}][] set value 1
execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run scoreboard players operation #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count1 {scoreboard_objective} -= #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count2 {scoreboard_objective}
execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.count1 {scoreboard_objective} matches 1.. run data modify storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time2}}}].value append value 1
''',**kwargs)

    def BoolOp_record(self,tree:ast,condition_time:int,index:int,func:str,*args,**kwargs):
        '''逻辑运算中 记录逻辑结果'''
        self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}].value','append',0,func,**kwargs)
        self.mcf_change_value_by_scoreboard(f'{defualt_STORAGE} main_tree[-1].boolResult[{{"id":{condition_time}}}].value',f'#{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{index} {scoreboard_objective}','int',1,func,**kwargs)


    def While(self,tree:ast.While,func:str,*args,**kwargs):
        '''While循环处理'''
        self.main_tree[-1]["while_time"] += 1
        # test
        ## while前 新建栈
        self.write_file(func,f'     ##while_begin   \n',**kwargs)
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run function {defualt_NAME}:{func}/while_{self.main_tree[-1]["while_time"]}/_start\n',**kwargs)
        self.mcf_old_stack_cover_data(func,**kwargs)
        self.mcf_remove_stack_data(func,**kwargs)
        self.write_file(func,f'     ##while_end     \n',**kwargs)

        kwargs_ = copy.deepcopy(kwargs)
        kwargs['def_function'] = False
        kwargs['p'] = f'{func}//while_{self.main_tree[-1]["while_time"]}//'
        kwargs['f2'] = f'_start'
        ## is_continue
        self.write_file(func,f'execute if data storage {defualt_STORAGE} main_tree[-1].is_continue run data remove storage {defualt_STORAGE} main_tree[-1].is_end\n',**kwargs)
        self.write_file(func,f'execute if data storage {defualt_STORAGE} main_tree[-1].is_continue run data remove storage {defualt_STORAGE} main_tree[-1].is_continue\n',**kwargs)
        #
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run function {defualt_NAME}:{func}/while_{self.main_tree[-1]["while_time"]}/condition/_start\n',**kwargs)
        

        kwargs['p'] = f'{func}//while_{self.main_tree[-1]["while_time"]}//condition//'
        # 类型扩建TODO
        if isinstance(tree.test,ast.Name):
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['def_function'] = False
            self.main_tree[-1]['condition_time'] = 0
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].data[{{"id":"{tree.test.id}"}}].value',func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.UnaryOp):
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['def_function'] = False
            self.main_tree[-1]['condition_time'] = 1
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            self.UnaryOp(tree.test,True,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)
        elif isinstance(tree.test,ast.Constant):
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['def_function'] = False
            self.main_tree[-1]['condition_time'] = 0
            self.main_tree[-1]['condition_time'] += 1
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":tree.test.value},func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)

            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.Compare):
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['def_function'] = False
            self.main_tree[-1]['condition_time'] = 0
            self.main_tree[-1]['condition_time'] += 1
            self.Compare(tree.test,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.main_tree[-1]['condition_time'] = 0
        elif isinstance(tree.test,ast.BoolOp):
            self.main_tree[-1]['condition_time'] = 0
            self.main_tree[-1]['condition_time'] += 1
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            self.BoolOp(tree.test,1,func,True,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
            self.BoolOp_operation(tree.test,0,0,func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolResult[{{"id":0}}][-1]\n',**kwargs)
            self.main_tree[-1]['condition_time'] = 0
        elif isinstance(tree.test,ast.Subscript):
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['def_function'] = False
            self.main_tree[-1]['condition_time'] += 1
            self.Subscript(tree.test,func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].Subscript.value',func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        elif isinstance(tree.test,ast.BinOp):
            self.main_tree[-1]['condition_time'] += 1
            self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
            kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
            kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
            kwargs['def_function'] = False
            self.BinOp(tree.test,tree.test.op,func,-1,-1,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].boolOPS','append',{"value":0},func,**kwargs)
            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value','set',f'storage {defualt_STORAGE} main_tree[-1].exp_operation[-1].value',func,**kwargs)
            self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute store result score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[-1].boolOPS[-1].value\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches 1.. run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)
            self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.temp {scoreboard_objective} matches ..0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 0\n',**kwargs)
        # body
        kwargs['p'] = f'{func}//while_{self.main_tree[-1]["while_time"]}//'
        kwargs['f2'] = f'_start'
        self.write_file(func,f'##while 主程序\n',**kwargs)
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run function {defualt_NAME}:{func}/while_{self.main_tree[-1]["while_time"]}/main\n',**kwargs)
        temp_value = self.main_tree[-1]["while_time"]
        self.walk(tree.body,func,-1,p=f'{func}//while_{self.main_tree[-1]["while_time"]}//',f2=f'main')
        self.write_file(func,f'function {defualt_NAME}:{func}/while_{temp_value}/_start\n',p=f'{func}//while_{temp_value}//',f2=f'main')

    def Break(self,tree:ast.Break,func,*args,**kwargs):
        '''Break 处理'''
        self.write_file(func,f'     # Break\n',**kwargs)
        self.mcf_stack_break(func,**kwargs)

    def Continue(self,tree:ast.Continue,func,*args,**kwargs):
        '''Continue 处理'''
        self.write_file(func,f'     # Continue\n',**kwargs)
        self.mcf_stack_continue(func,**kwargs)
    
    def get_condition_reverse(self,func,*args,**kwargs):
        '''条件取反'''
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass_ {scoreboard_objective} 0\n',**kwargs)
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} matches 0 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass_ {scoreboard_objective} 1\n',**kwargs)
        self.mcf_reset_score(f'#{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}',func,**kwargs)
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run scoreboard players operation #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} = #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass_ {scoreboard_objective}\n',**kwargs)

    def For(self,tree:ast.For,func:str,*args,**kwargs):
        '''for循环 处理'''
        self.main_tree[-1]["for_time"] += 1
        # test
        ## for前 新建栈
        self.write_file(func,f'     ##for_begin   \n',**kwargs)
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run function {defualt_NAME}:{func}/for_{self.main_tree[-1]["for_time"]}/_start\n',**kwargs)
        self.mcf_old_stack_cover_data(func,**kwargs)
        self.mcf_remove_stack_data(func,**kwargs)
        self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-1].data[{{"temp":1b}}]','remove','',func,**kwargs)
        self.write_file(func,f'     ##for_end     \n',**kwargs)

        kwargs_ = copy.deepcopy(kwargs)

        kwargs['def_function'] = False
        kwargs['p'] = f'{func}//for_{self.main_tree[-1]["for_time"]}//'
        kwargs['f2'] = f'_start'
        ##初始化 迭代器列表
        self.write_file(func,f'#迭代器初始化\n',**kwargs)
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run function {defualt_NAME}:{func}/for_{self.main_tree[-1]["for_time"]}/iterator/_init\n',**kwargs)
        ## is_continue
        kwargs['f2'] = f'main'
        self.write_file(func,f'execute if data storage {defualt_STORAGE} main_tree[-1].is_continue run data remove storage {defualt_STORAGE} main_tree[-1].is_end\n',**kwargs)
        self.write_file(func,f'execute if data storage {defualt_STORAGE} main_tree[-1].is_continue run data remove storage {defualt_STORAGE} main_tree[-1].is_continue\n',**kwargs)
        #
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run function {defualt_NAME}:{func}/for_{self.main_tree[-1]["for_time"]}/iterator/_start\n',**kwargs)
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
        self.write_file(func,f'execute unless data storage {defualt_STORAGE} main_tree[-1].is_end run function {defualt_NAME}:{func}/for_{self.main_tree[-1]["for_time"]}/main\n',**kwargs)
        temp_value = self.main_tree[-1]["for_time"]
        ## 
        self.walk(tree.body,func,-1,p=f'{func}//for_{self.main_tree[-1]["for_time"]}//',f2=f'main')
        ##
        self.write_file(func,f'execute if data storage {defualt_STORAGE} main_tree[-1].for_list[0] run function {defualt_NAME}:{func}/for_{temp_value}/main\n',p=f'{func}//for_{temp_value}//',f2=f'main')


# 逻辑调用

    def BoolOP_call(self,value:ast.boolop,func:str,*args,**kwargs):
        """boolop调用\n
        返回 处理storage {defualt_STORAGE} main_tree[-1].boolResult[{{\"id\":0}}][-1]"""
        self.main_tree[-1]['condition_time'] += 1
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
        kwargs['f2'] = f'{self.main_tree[-1]["condition_time"]}'
        kwargs['p'] = f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//'
        kwargs['def_function'] = False
        self.BoolOp(value,0,func,True,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
        self.BoolOp_operation(value,0,0,func,**kwargs)

    def Compare_call(self,value:ast.Compare,func:str,*args,**kwargs):
        """Compare调用\n
        返回处理\n 
        self.mcf_store_value_by_run_command(f' int 1',f'scoreboard players get #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective}',func,**kwargs)
        """
        self.main_tree[-1]['condition_time'] += 1
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
        self.Compare(value,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
        self.write_file(func,f'execute if score #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective} matches 1 run scoreboard players set #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} 1\n',**kwargs)

    def UnaryOp_call(self,value:ast.UnaryOp,func:str,*args,**kwargs):
        """UnaryOp调用"""
        self.mcf_new_stack(func,**kwargs)
        self.mcf_new_stack_inherit_data(func,**kwargs)
        self.main_tree[-1]['condition_time'] += 1
        self.write_file(func,f'function {defualt_NAME}:{func}/condition_{(self.main_tree[-1]["BoolOpTime"])}/if/{self.main_tree[-1]["condition_time"]}\n',**kwargs)
        self.UnaryOp(value,True,self.main_tree[-1]["condition_time"],func,p=f'{func}//condition_{(self.main_tree[-1]["BoolOpTime"])}//if//',f2=f'{self.main_tree[-1]["condition_time"]}')
        self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.pass {scoreboard_objective} = #{defualt_NAME}.system.c.{(self.main_tree[-1]["BoolOpTime"])}.{self.main_tree[-1]["condition_time"]} {scoreboard_objective}\n',**kwargs)



















class System_function(Parser):
    '''内置函数 处理器'''
    def __init__(self,*args,**kwargs) -> None:
        '''storage名称 nbt'''
        if len(args) >= 3:
            self.main_tree,self.func_name,self.func = tuple(args[0:3])
    def main(self,*args,**kwargs):
        if self.func_name == 'print':
            self.print(self.func,**kwargs)
            self.mcf_remove_stack_data(self.func,**kwargs)
        elif self.func_name == 'range':
            self.range(self.func,**kwargs)
            self.mcf_remove_stack_data(self.func,**kwargs)
        else:
            # 自定义函数
            for item in system_functions:
                if item['name'] == self.func_name:
                    self.write_file(self.func,f'#参数处理.赋值\n',**kwargs)
                    for i in range(len(item['args'])):
                        if item['args'][i]['type'] == 'storage':
                            self.write_file(self.func,f"data modify storage {item['args'][i]['name']} set from storage {defualt_STORAGE} main_tree[-1].call_list[{i}].value\n",**kwargs)
                    self.write_file(self.func,f'#函数调用\n',**kwargs)
                    self.write_file(self.func,f"function {item['call_path']}\n",**kwargs)
                    if item['return']['type'] == 'storage':
                            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return','append',{"value":0},self.func,**kwargs)
                            self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-2].return[-1].value','set',f"storage {item['return']['name']}",self.func,**kwargs)
                    self.mcf_remove_stack_data(self.func,**kwargs)

    def print(self,func,*args,**kwargs):
        self.write_file(func,f'#参数处理.赋值\n',**kwargs)
        self.write_file(func,f'#函数调用\n',**kwargs)
        self.write_file(func,f'tellraw @a [',**kwargs)
        for i in range(len(self.main_tree[-1]["call_list"])):
            value = RawJsonText(MCStorage('storage',f'{defualt_STORAGE}',f'main_tree[-1].call_list[{i}].value'))
            self.write_file(func,f'{value}',func,**kwargs)
            if i >= 0 and i < len(self.main_tree[-1]["call_list"]) - 1:
                self.write_file(func,'," ",',func,**kwargs)
        self.write_file(func,f']\n',**kwargs)
        
        self.write_file(func,f'##函数调用_end\n',**kwargs)
    def range(self,func,*args,**kwargs):
        self.write_file(func,f'#参数处理.赋值\n',**kwargs)
        self.write_file(func,f'#函数调用\n',**kwargs)
        handle = True
        range_list = []
        for i in self.main_tree[-1]["call_list"]:
            if not i["is_constant"]:
                handle = False
            range_list.append(i["value"])
        mcf_range_list = []
        if handle:
            for i in range(*range_list):
                mcf_range_list.append({"value":i})
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].return','append',{"value":0},self.func,**kwargs)
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].return[-1].value','set',mcf_range_list,self.func,**kwargs)
        else:
            self.write_file(func,f'data modify storage t_algorithm_lib:array range.input set from storage {defualt_STORAGE} main_tree[-1].call_list[0].value\n',**kwargs)
            self.write_file(func,f'function t_algorithm_lib:array/range/start\n',**kwargs)
        self.write_file(func,f'##函数调用_end\n',**kwargs)




class Custom_function(Parser):
    '''自定义函数 处理器'''
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
                                self.write_file(func,f"data modify storage {item2['args'][i]['name']} set from storage {defualt_STORAGE} main_tree[-1].call_list[{i}].value\n",**kwargs)
                        self.write_file(func,f'#函数调用\n',**kwargs)
                        self.write_file(func,f"function {item2['call_path']}\n",**kwargs)
                        if item2['return']['type'] == 'storage':
                                self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-2].return','append',{"value":0},func,**kwargs)
                                self.mcf_modify_value_by_from(f'storage {defualt_STORAGE} main_tree[-2].return[-1].value','set',f"storage {item2['return']['name']}",func,**kwargs)
                        return True
        #无
        return False


class mc_function(Parser):
    '''系统函数'''
    def __init__(self,main_tree):
        self.main_tree = main_tree
    def get_value(self,arg:ast,func,*args,**kwargs):
        if isinstance(arg,ast.Constant):
            return arg.value
        elif isinstance(arg,ast.Name):
            return self.py_get_value(arg.id,func,**kwargs)
    def main(self,func_name,arg,func,*args,**kwargs):
        print(func_name,arg,func)
        if(func_name == 'run'):
            command = self.get_value(arg[0],func,**kwargs) if len(arg) >= 1 else "say hello world"
            flag = self.get_value(arg[1],func,**kwargs) if len(arg) >= 2 else "result"
            self.mcf_modify_value_by_value(f'storage {defualt_STORAGE} main_tree[-1].return','append',{"value":0},func,**kwargs)
            self.write_file(func,f"execute store {flag} storage {defualt_STORAGE} main_tree[-1].return[-1].value double 1.0 run {command}\n",**kwargs)
        elif(func_name == 'example'):
            ...
        elif(func_name == 'rebuild'):
            ...


