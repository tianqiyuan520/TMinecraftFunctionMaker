import json

class read_json:
    def __init__(self,path):
        ...
    def read(path) -> json: 
        with open(path,"r",encoding='utf-8') as f:
            file = json.load(f)
        return file


def run(command:str = "say hello world",flag:str="result"):
    """
        - 执行mc指令
        
        example:
        
        >>> run('say hi') 
        #将在mcfunction写入say hi
        >>> a = run('say hi') 
        #将在mcfunction写入execute store result ... run say hi . 将命令执行结果返回给变量a
        >>> a = run('say hi','success') 
        #将在mcfunction写入execute store success ... run say hi . 将命令执行结果返回给变量a
        
    """

    return 0.0

def NewFunction(name=None,path=None) -> None:
    """
        新建函数
        - 默认在 {数据包}\\{命名空间}\\functions\\path 下
        - name 为函数名(例如:"a","test") 
        - path 为相对路径加函数名(例如:"x\\","test2\\")

        example:
        >>> NewFunction(name="test",path="abc\\xc\\")
        
        将在 {数据包}\\{命名空间}\\functions\\abc\\xc\\ 下 创建函数 test.mcfunction
    """

def WriteFunction(name=None,Command=None,mode=None,path=None) -> None:
    """
        将命令写入函数中
        - 默认在 {数据包}\\{命名空间}\\functions\\path 下
        - name 为函数名(例如:"a","test") 
        - path 为相对路径加函数名(例如:"x\\","test2\\")
        - Command  数组 (例如：["say 1","say 2"])
        - mode： "w"覆写，"a"追加 默认追加

        example:
        >>> WriteFunction("test",["say 1"],"a","abc\\xc\\")
        
        将在 {数据包}\\{命名空间}\\functions\\abc\\xc\\test 中 写入 say 1
    """

def newTags(TagName=None,NameSpace=None,Value=None,Path=None) -> None:
    """
        新建 标签 （ 命名空间/Tags/XX ）
        - 默认在 {数据包}\\{命名空间}\\Tags\\ 下
        - Value 命名空间 + 函数名称 的 数组 (例如:["test:load/_start","test:xx"...]) 
        - Path 为相对路径加函数名(例如:"x\\","test2\\")
        - TagName 标签名称

        example:
        >>> newTags("load","minecraft",["test:a"],"functions\\3")
        
        将在 {数据包}\\minecraft\\Tags\\functions\\3\\load 下 写入 ["test:a"]
    """


def checkBlock(Pos:list=None,BlockId:str=None) -> bool:
    """
        判断 给定坐标的方块是否为指定方块
        - 返回1/0
        - Pos 坐标
        - BlockId 方块ID

        example:
        >>> checkBlock("0 0 0","minecraft:air")
    """

## 工具 类


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


class MCEntity:
    '''实体类型
    
    实例化一个实体，返回UUID
    '''
    def __init__(self,EntityName=None,Pos=None,Nbt=None,UUID=None) -> None:
        '''可以指定 生成的实体类型，坐标，nbt，UUID
        
        >>> 默认生成
        - 实体:area_effect_cloud
        - 坐标:~ ~ ~
        - nbt:{}
        - UUID:随机UUID

        返回该实体的UUID（IntArray）
        '''
    def get_data(self,DataName=None):
        '''
        获取实体数据
        
        类似data get entity XX xx
        '''
        return 0.0
