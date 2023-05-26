import math
import re
from enum import Enum,auto


class TokenType(Enum):
    FUNC_CALL = auto()#函数调用
    EQUALS = auto()
    NUMBER = auto()
    IDENTIFIER = auto()##标识符
    STRING = auto()#字符串
    BINARY_OPERATER = auto()
    OPEN_PAREN = auto()#左括号
    CLOSE_PAREN = auto()#右括号
    SPACE = auto()#空格
    EOF = auto() #判断完成 end of find

TOKEN_REGEX={
    TokenType.FUNC_CALL:r'[a-z_A-Z][a-z_A-Z_0-9]*\(.*?\)',
    TokenType.NUMBER:r'[0-9]+[0-9]*',
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


class TMCFM:
    def __init__(self,content):
        print('init...')
        self.content = content
        print('content: \n',content)
        print('init success')
    
    def main(self):
        tokenize(self.content)
        self.parse(self.content)
        ...
    


    def parse(self,value:list) -> list:
        '''解析'''
    #读取 func
    ## [  {name:"",content:[]} ]
    
        func = []
        find = False
        for i in value:
            if find:
                if len(i) >= 1 and i[0] != " ":
                    find = False
                else:
                    func[-1]["content"].append(i)
            if not find and len(i) >= 1 and i[0:3] == "def":
                find = True
                func.append({"name":"","content":[]})
                ##正则
                pattern = re.compile(r'.*\({0}')
                result = pattern.findall(i,4)
                func[-1]["name"] = result[0][0:-3]
        print(func,find)

    def handle_fuc(self,value:list) -> list:
        ##详细处理函数
        
        ...

