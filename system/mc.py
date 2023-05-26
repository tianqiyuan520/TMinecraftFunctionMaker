from read_config import read_json


def run(command:str = "say hello world",flag:str="result"):
    """
        - 执行mc指令
        
        example:
        
        run('say hi') #将在mcfunction写入say hi
        
        a = run('say hi') #将在mcfunction写入execute store result ... run say hi . 将命令执行结果返回给变量a
        
        a = run('say hi','success') #将在mcfunction写入execute store success ... run say hi . 将命令执行结果返回给变量a
        
    """

    return 0.0

def rebuild() -> bool:
    """
        重建 数据包
    """
    return True

## 工具


# def RawJsonText(text,*args,**kwargs) -> str:
#     """原始json文本化 """
#     if 'commend' in dir(self) and not 'file' in dir(self):
#         if self.commend.type == 'score':
#             return f'{{"score":{{"name":"{self.commend.name}","objective":"{self.commend.nbt}"}}}}'
#         elif self.commend.type == 'storage' or self.commend.type == 'block' or self.commend.type == 'entity':
#             return f'{{"nbt":"{self.commend.nbt}","{self.commend.type}":"{self.commend.name}"}}'
#         else:
#             return '{}'
#     elif 'file' in dir(self):
#         #解析 json文件 转 原始json文本
#         return str(read_json.read(self.file)).replace("'",'"')
#     else:
#         return '{}'