
from model.file_ops import read_json
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
