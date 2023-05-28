from read_config import read_json,System_i_functions
from custom_function_parser import Custom_Fuc_Parser

defualt_PATH = '' #默认路径
defualt_STORAGE = '' # STORAGE
scoreboard_objective = '' # 默认记分板
defualt_NAME = '' # 项目名称
system_functions = System_i_functions.read() # 内置函数调用表
custom_functions = Custom_Fuc_Parser.read() # 自定义函数调用表

cfg = read_json.read('config.json')['config']
scoreboard_objective = cfg['scoreboard_objective']
defualt_NAME = cfg['name']
defualt_DataPath = cfg['path']+"data\\"
defualt_PATH = cfg['path']+"data\\"+cfg['name'] + '\\'
defualt_STORAGE = cfg['name']+":system"