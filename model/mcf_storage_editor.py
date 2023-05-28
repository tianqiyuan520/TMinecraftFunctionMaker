import ast
import os

from config import defualt_PATH #默认路径
from config import defualt_STORAGE # STORAGE
from config import scoreboard_objective # 默认记分板
from config import defualt_NAME # 项目名称

class Storage_editor:
    '''有光mcf storage的修改'''
    def __init__(self) -> None:
        pass
    def write_file(self,func:str,text,*args,**kwargs):
        '''写文件 f2为函数详细名称,p为函数的相对位置'''
        func2 = '_start'
        PATH_ = None
        for key, value in kwargs.items():
            if(key=='f2'or key ==  'func2'):
                func2 = value
            if(key=='p'or key ==  'path'):
                PATH_ = value
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

    def mcf_change_value(self,key,value,is_global:False,func:str,isfundef:False,index:-1,*args,**kwargs):
        '''修改mcf中的堆栈值 常量修改'''
        if isinstance(value,str):
            value = "\""+str(value)+"\""
        if not isfundef:
            if(is_global):
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value set value {value}\n',**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}].value set value {value}\n',**kwargs)
        else:
            if(is_global):
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute unless data storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}] run data modify storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value set value {value}\n',**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute unless data storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}] run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}].value set value {value}\n',**kwargs)

    def mcf_change_value2(self,key,key2,is_global:False,func:str,isfundef:False,index:-1,index2:-1,*args,**kwargs):
        '修改mcf中的堆栈值 变量修改'
        if not isfundef:
            if(is_global):
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value set from storage {defualt_STORAGE} main_tree[{index2}].data[{{"id":{key2}}}].value\n',**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}].value set from storage {defualt_STORAGE} main_tree[{index2}].data[{{"id":{key2}}}].value\n',**kwargs)
        else:
            if(is_global):
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute unless data storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}] run data modify storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value set from storage {defualt_STORAGE} main_tree[{index2}].data[{{"id":{key2}}}].value\n',**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute unless data storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}] run data modify storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}].value set from storage {defualt_STORAGE} main_tree[{index2}].data[{{"id":{key2}}}].value\n',**kwargs)

    def mcf_add_exp_operation(self,value,func,index:-1,*args,**kwargs):
        '''mcf 表达式运算过程中添加值 变量添加'''
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[{index}].exp_operation append value {{"value":{value},"type":"num"}}\n',**kwargs)

    def mcf_add_exp_operation2(self,value,func,index:-1,index2:-1,*args,**kwargs):
        '''mcf 表达式运算过程中添加值 返回值添加'''
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[{index}].exp_operation append from storage {defualt_STORAGE} main_tree[-1].return[{index2}]\n',**kwargs)

    def mcf_change_exp_operation(self,operation,func,index:-1,*args,**kwargs):
        '''mcf 表达式运算过程中修改值 数值运算'''
        self.write_file(func,
        f'''execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[{index}].exp_operation[-2].value 1000
execute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value 1000
''',**kwargs)
        if isinstance(operation,ast.Add):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value double 0.001 run scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} += #{defualt_NAME}.system.temp2 {scoreboard_objective}\n',**kwargs)
        elif isinstance(operation,ast.Sub):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value double 0.001 run scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} -= #{defualt_NAME}.system.temp2 {scoreboard_objective}\n',**kwargs)
        elif isinstance(operation,ast.Mult):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value double 0.000001 run scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} *= #{defualt_NAME}.system.temp2 {scoreboard_objective}\n',**kwargs)
        elif isinstance(operation,ast.Div):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[{index}].exp_operation[-2].value 1000000\n',**kwargs)
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {defualt_STORAGE} main_tree[{index}].exp_operation[-1].value double 0.001 run scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} /= #{defualt_NAME}.system.temp2 {scoreboard_objective}\n',**kwargs)
        elif isinstance(operation,ast.Pow):
            self.write_file(func,f'次方运算\n')
        self.write_file(func,
        f'''execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} main_tree[{index}].exp_operation[-2]
''',**kwargs)

    def mcf_change_value_by_operation(self,key,key2,is_global:False,op:ast.operator,func:str,index:-1,*args,**kwargs):
        '修改mcf中的堆栈值 变量修改 += -= *= /='
        if isinstance(op,ast.Add):
            self.write_file(func,
            f'''execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value 1000
execute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[{index}].data[{{"id":{key2}}}].value 1000
execute store result storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}].value double 0.001 run scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} += #{defualt_NAME}.system.temp2 {scoreboard_objective}
''',**kwargs)
            if(is_global):
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value double 0.001 run scoreboard players get #{defualt_NAME}.system.temp1 {scoreboard_objective}\n',**kwargs)
        if isinstance(op,ast.Sub):
            self.write_file(func,
            f'''execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value 1000
execute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[{index}].data[{{"id":{key2}}}].value 1000
execute store result storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}].value double 0.001 run scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} -= #{defualt_NAME}.system.temp2 {scoreboard_objective}
''',**kwargs)
            if(is_global):
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value double 0.001 run scoreboard players get #{defualt_NAME}.system.temp1 {scoreboard_objective}\n',**kwargs)
        if isinstance(op,ast.Mult):
            self.write_file(func,
            f'''execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value 1000
execute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[{index}].data[{{"id":{key2}}}].value 1000
execute store result storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}].value double 0.000001 run scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} *= #{defualt_NAME}.system.temp2 {scoreboard_objective}
''',**kwargs)
            if(is_global):
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}].value double 0.000001 run scoreboard players get #{defualt_NAME}.system.temp1 {scoreboard_objective}\n',**kwargs)
        if isinstance(op,ast.Div):
            self.write_file(func,
            f'''execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value 1000000
execute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {defualt_STORAGE} main_tree[{index}].data[{{"id":{key2}}}].value 1000
execute store result storage {defualt_STORAGE} main_tree[{index}].data[{{"id":"{key}"}}].value double 0.001 run scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} /= #{defualt_NAME}.system.temp2 {scoreboard_objective}
''',**kwargs)
            if(is_global):
                self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {defualt_STORAGE} main_tree[0].data[{{"id":"{key}"}}].value double 0.001 run scoreboard players get #{defualt_NAME}.system.temp1 {scoreboard_objective}\n',**kwargs)
        if isinstance(op,ast.Pow):
            self.write_file(func,
            f'''次方运算
''',**kwargs)
            if(is_global):
                self.write_file(func,f'次方运算\n',**kwargs)
    def mcf_change_value_by_operation2(self,Storage,Storage2,Storage3,op:ast.operator,func:str,index:-1,*args,**kwargs):
        '''修改mcf中的堆栈值 Storage 修改 += -= *= /='''
        if isinstance(op,ast.Add):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {Storage} 1000\nexecute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {Storage2} 1000\n',**kwargs)
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} += #{defualt_NAME}.system.temp2 {scoreboard_objective}\nexecute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {Storage3} double 0.001 run scoreboard players get #{defualt_NAME}.system.temp1\n',**kwargs)
        elif isinstance(op,ast.Sub):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {Storage} 1000\nexecute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {Storage2} 1000\n',**kwargs)
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} += #{defualt_NAME}.system.temp2 {scoreboard_objective}\nexecute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {Storage3} double 0.001 run scoreboard players get #{defualt_NAME}.system.temp1\n',**kwargs)
        elif isinstance(op,ast.Mult):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {Storage} 1000\nexecute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {Storage2} 1000\n',**kwargs)
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} += #{defualt_NAME}.system.temp2 {scoreboard_objective}\nexecute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {Storage3} double 0.000001 run scoreboard players get #{defualt_NAME}.system.temp1\n',**kwargs)
        elif isinstance(op,ast.Div):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {Storage} 1000000\nexecute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {Storage2} 1000\n',**kwargs)
            self.write_file(func,f'scoreboard players operation #{defualt_NAME}.system.temp1 {scoreboard_objective} += #{defualt_NAME}.system.temp2 {scoreboard_objective}\nexecute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {Storage3} double 0.001 run scoreboard players get #{defualt_NAME}.system.temp1\n',**kwargs)

    def mcf_change_value_by_storage(self,Storage,Storage2,func:str,*args,**kwargs):
        '''storage = storage'''
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {Storage} set from storage {Storage2}\n',**kwargs)

    def mcf_modify_value_by_from(self,Storage,flag:str,VALUE_FROM,func:str,*args,**kwargs):
        '''\n
        storage/block/entity .. \n
        flag: append / insert [num] / merge / prepend / set / remove \nVALUE_FROM(有来源的修改)'''
        if(flag!='remove'):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {Storage} {flag} from {VALUE_FROM}\n',**kwargs)
        else:
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove {Storage}\n',**kwargs)

    def mcf_modify_value_by_value(self,Storage,flag,VALUE,func:str,*args,**kwargs):
        '''storage append / insert [num] / merge / prepend / set VALUE(无来源的修改，直接修改)'''
        if isinstance(VALUE,str):
            VALUE = "\""+r'%s'%(VALUE)+"\""
        if isinstance(VALUE,dict):
            VALUE = str(VALUE).replace("'",'"')
        if isinstance(VALUE,list) and "'" in str(VALUE):
            VALUE = str(VALUE).replace("'",'"')
        if(flag!='remove'):
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify {Storage} {flag} value {VALUE}\n',**kwargs)
        else:
            self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove {Storage}\n',**kwargs)

    def mcf_store_value_by_run_command(self,VALUE,command,func:str,flag='result',*args,**kwargs):
        '''store'''
        self.write_file(func,f'execute store {flag} {VALUE} run {command}\n',**kwargs)


    def mcf_change_value_by_scoreboard(self,Storage,scoreboard,type:str,scale:str,func:str,*args,**kwargs):
        '''storage = scoreboard'''
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result storage {Storage} {type} {scale} run scoreboard players get {scoreboard}\n',**kwargs)
    
    def mcf_compare_Svalues(self,Storage,Storage2,flag,func,command,*args,**kwargs):
        '''比较 两个 storage值的大小'''
        if isinstance(flag,ast.Gt):
            #大于
            self.write_file(func,
            f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {Storage} 1000\nexecute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {Storage2} 1000\nexecute if score #{defualt_NAME}.system.temp1 {scoreboard_objective} > #{defualt_NAME}.system.temp2 {scoreboard_objective} run {command}\n',**kwargs)
        elif isinstance(flag,ast.Lt):
            #小于
            self.write_file(func,
            f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {Storage} 1000\nexecute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {Storage2} 1000\nexecute if score #{defualt_NAME}.system.temp1 {scoreboard_objective} < #{defualt_NAME}.system.temp2 {scoreboard_objective} run {command}\n',**kwargs)
        elif isinstance(flag,ast.Eq):
            #等于
            self.write_file(func,
            f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store success score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data modify storage {Storage} set from storage {Storage2} \nexecute if score #{defualt_NAME}.system.temp1 {scoreboard_objective} matches 0 run {command}\n',**kwargs)
        elif isinstance(flag,ast.GtE):
            #大于或等于
            self.write_file(func,
            f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {Storage} 1000\nexecute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {Storage2} 1000\nexecute if score #{defualt_NAME}.system.temp1 {scoreboard_objective} >= #{defualt_NAME}.system.temp2 {scoreboard_objective} run {command}\n',**kwargs)
        elif isinstance(flag,ast.LtE):
            #小于或等于
            self.write_file(func,
            f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store result score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data get storage {Storage} 1000\nexecute store result score #{defualt_NAME}.system.temp2 {scoreboard_objective} run data get storage {Storage2} 1000\nexecute if score #{defualt_NAME}.system.temp1 {scoreboard_objective} <= #{defualt_NAME}.system.temp2 {scoreboard_objective} run {command}\n',**kwargs)
        elif isinstance(flag,ast.NotEq):
            #不等于
            self.write_file(func,
            f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run execute store success score #{defualt_NAME}.system.temp1 {scoreboard_objective} run data modify storage {Storage} set from storage {Storage2} \nexecute if score #{defualt_NAME}.system.temp1 {scoreboard_objective} matches 1 run {command}\n',**kwargs)

    def mcf_new_stack(self,func,*args,**kwargs):
        '''新建栈'''
        self.write_file(func,f'#新建栈\n',**kwargs)
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree append value {{"data":[],"return":[],"type":"","exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"list_handler":[]}}\n',**kwargs)
        
    def mcf_new_stack_inherit_data(self,func,*args,**kwargs):
        '''新建的栈 继承上一个栈值的data数据'''
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-1].data set from storage {defualt_STORAGE} main_tree[-2].data\n',**kwargs)

    def mcf_old_stack_cover_data(self,func,*args,**kwargs):
        '''上一个栈 覆盖原先的data数据 ，新的data来自 新建的栈'''
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data modify storage {defualt_STORAGE} main_tree[-2].data set from storage {defualt_STORAGE} main_tree[-1].data\n',**kwargs)
    def mcf_remove_stack_data(self,func:str,*args,**kwargs):
        '''出栈'''
        self.write_file(func,f'execute unless score #{defualt_STORAGE}.stack.end {scoreboard_objective} matches 1 run data remove storage {defualt_STORAGE} main_tree[-1]\n',**kwargs)

    def mcf_stack_break(self,func:str,*args,**kwargs):
        '''栈 中 break'''
        self.write_file(func,f'scoreboard players set #{defualt_STORAGE}.stack.end {scoreboard_objective} 1\n',**kwargs)
        self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_break set value 1b\n',**kwargs)

    def mcf_stack_continue(self,func:str,*args,**kwargs):
        '''栈 中 continue'''
        self.write_file(func,f'scoreboard players set #{defualt_STORAGE}.stack.end {scoreboard_objective} 1\n',**kwargs)
        self.write_file(func,f'data modify storage {defualt_STORAGE} main_tree[-1].is_continue set value 1b\n',**kwargs)

    def mcf_reset_score(self,value,func,**kwargs):
        '''重置实体记分板值'''
        self.write_file(func,f'scoreboard players reset {value}\n',**kwargs)




