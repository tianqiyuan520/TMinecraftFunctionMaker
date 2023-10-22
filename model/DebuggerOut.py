import os
import time

from read_config import read_json
from model.file_ops import editor_file

class DebuggerOut:
    '''Debug输出
    
    - 输出到配置文件中 logPath 下的 log.txt

    path = [__file__,sys._getframe().f_lineno]
    '''
    def __init__(self,text="",path=None,wrong=False,**kwargs) -> None:
        cfg = read_json.read('config.json')['config']
        folder = os.path.exists(cfg["logPath"])
        if cfg["logPath"] != "" and not folder:
            os.makedirs(cfg["logPath"])
        
        with open(cfg["logPath"] + 'log.txt','a',encoding='utf-8') as f:
            if not wrong:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {text} \n")
            else:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {text} in File \"{path[0]}\", line {path[1]}\n")

class Logger(editor_file):
    def __init__(self,func,text,**kwargs):
        self.write_file(func,f'#{text}\n',**kwargs)