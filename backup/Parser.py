
import copy
import re
import ast

from enum import Enum,auto
from TMCFM import D_PATH

defualt_PATH = D_PATH+'functions\\'+'load.mcfunction' #默认函数

class TokenType(Enum):
    FUNC_CALL = auto()#函数调用
    FUNC_DEF = auto()#函数定义
    EQUALS = auto()
    INT = auto()
    FLOAT = auto()
    IDENTIFIER = auto()##标识符
    STRING = auto()#字符串
    BINARY_OPERATER = auto()
    OPEN_PAREN = auto()#左括号
    CLOSE_PAREN = auto()#右括号
    SPACE = auto()#空格
    EOF = auto() #判断完成 end of find

TOKEN_REGEX={
    TokenType.FUNC_DEF:r'def [a-z_A-Z][a-z_A-Z_0-9]*\(.*?\):',
    TokenType.FUNC_CALL:r'[a-z_A-Z][a-z_A-Z_0-9]*\(.*?\)',
    TokenType.FLOAT:r'[0-9]+[0-9]*\.[0-9]+[0-9]*',
    TokenType.INT:r'[0-9]+[0-9]*',
    TokenType.IDENTIFIER:r'[a-z_A-Z][a-z_A-Z_0-9]*',
    TokenType.BINARY_OPERATER:r'[+\-*/%]',
    TokenType.EQUALS:r'=',
    TokenType.OPEN_PAREN:r'\(',
    TokenType.CLOSE_PAREN:r'\)',
    TokenType.STRING:r'".*?"',
    TokenType.SPACE:r'[ \t\r]'
}

class Token:
    def __init__(self,type:TokenType,value) -> None:
        self.type:TokenType = type
        self.value:str = value
    def __repr__(self) -> str:
        return f'{{ {self.type} , {self.value} }}'

def tokenize(code:str):
    ###读取，并将这个转化为token
    tokens : list[Token] = []
    ##正则匹配
    match = None
    while code:
        for tokentype,pattern in TOKEN_REGEX.items():
            match = re.match(pattern,code)
            if match:
                value = match.group()
                ##刷新code
                code = code[len(value):]
                if tokentype == TokenType.SPACE:
                    continue
                elif tokentype == TokenType.STRING:
                    tokens.append(Token(tokentype,value[1:-1]))
                else:
                    tokens.append(Token(tokentype,value))
                break
        if match == None:
            #无匹配报错
            raise Exception(__file__,'Not valid charater无效字符',code[0])
    tokens.append(Token(TokenType.EOF,'end of find'))
    for i in tokens:
        print(i)


class Parser:
    '''解析程序'''
    def __init__(self,content) -> None:
        self.code = content
        #模拟栈 [{  "data":[{"id":"x","value":""},{...}],"is_end":0,"is_return":0,"is_break":0,"is_continue":0,"return":[{"id":"x","value":""}],"type":""  }]
        ##data为记录数据,is_return控制当前函数是否返回,is_end控制该函数是否终止,is_break控制循环是否终止,is_continue是否跳过后续的指令,return
        self.stack_frame = [{"data":[],"is_break":0,"is_continue":0,"return":[],"type":"","is_return":0,"is_end":0}]
        self.parse()
    def parse(self):
        code = copy.deepcopy(self.code)
        code_ = ast.parse(code)
        print(ast.dump(code_))
        #遍历python的ast树
        self.walk(code_.body)
        # for i in code:
        #     print(i)
        #     tokenize(i)
    def walk(self,tree:list = []):
        for item in tree:
            #如果是赋值
            if isinstance(item,ast.Assign):
                self.Assign(item)
                
    def BinOp(self,tree:ast.BinOp,op:ast.operator()):
        '''运算操作
        tree新的树，op操作类型 +-*/
        '''
        ##判断左右值，是否都为常数时才

        ...
    def Assign(self,tree:ast.Assign):
        '''赋值操作'''
        if isinstance(tree.value,ast.BinOp):
            self.BinOp(tree.value,tree.value.op)
    
    def write_file(self,path,text):
        '''写文件'''
        with open(path,'a') as f:
            f.write(text)