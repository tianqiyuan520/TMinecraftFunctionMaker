import json

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

class MCStorage:
    '''Minecraft 的 storage'''
    def __init__(self,*args,**kwargs):
        '''storage名称 nbt'''
        if len(args) >= 3:
            self.type,self.name,self.nbt = args[0:3]
        else:
            raise BaseException('MCStorage 参数 数量小于3')
    def __str__(self,*args,**kwargs) -> str:
        return f'{self.type} {self.name} {self.nbt}'

class RawJsonText:
    '''Minecraft 的 原始JSON文本'''
    def __init__(self,*args,**kwargs):
        if len(args) > 0:
            self.commend:MCStorage = args[0]
        for key,value in kwargs.items():
            if key=='color':
                self.color:str = value
            elif key=='font':
                self.font:str = value
            elif key=='bold':
                self.bold:bool = value
            elif key=='italic':
                self.italic:bool = value
            elif key=='underlined':
                self.underlined:bool = value
            elif key=='strikethrough':
                self.strikethrough:bool = value
            elif key=='obfuscated':
                self.obfuscated:bool = value
            elif key=='file':
                self.file:str = value

    def __str__(self,*args,**kwargs) -> str:
        if 'commend' in dir(self) and not 'file' in dir(self):
            if self.commend.type == 'score':
                return f'{{"score":{{"name":"{self.commend.name}","objective":"{self.commend.nbt}"}}}}'
            elif self.commend.type == 'storage' or self.commend.type == 'block' or self.commend.type == 'entity':
                return f'{{"nbt":"{self.commend.nbt}","{self.commend.type}":"{self.commend.name}"}}'
            else:
                return '{}'
        elif 'file' in dir(self):
            #解析 json文件 转 原始json文本
            return str(read_json.read(self.file)).replace("'",'"')
        else:
            return '{}'

class IntArray:
    def __init__(self,*args,**kwargs):
        if len(args) > 0:
            self.list:list = args[0]
    def __str__(self,*args,**kwargs) -> str:
        x = '[I; '
        for i in range(len(self.list)):
            x += str(self.list[i]).replace("'",'"')
            if i < len(self.list)-1:
                x += ', '
        x += ']'
        return x

class MCNbt():
    def __init__(self,*args,**kwargs):
        self.main:dict = kwargs
    def __str__(self,*args,**kwargs) -> str:
        x = '{'
        for key,value in self.main.items():
            x+='"' + str(key).replace("'",'"') + '"'
            x+=' : '
            if isinstance(value,str):
                if value[0] == "[" or value[0] == '{':
                    x+=(value)
                else:
                    x+='"' + str(value).replace("'",'"') + '"'
            else:
                x+=str(value).replace("'",'"')
            x+=', '
        x = x[0:-2]
        x += '}'
        return x

