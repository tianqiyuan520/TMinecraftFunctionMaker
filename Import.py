import copy
import json
import re
import ast
import os
from read_config import read_json
from model.mcf_modifier import mcf_modifier
from model.mc_nbt import MCStorage,RawJsonText,IntArray,MCNbt
from model.uuid_generator import get_uuid,uuid_to_list


from config import defualt_PATH #默认路径
from config import defualt_STORAGE # STORAGE
from config import scoreboard_objective # 默认记分板
from config import defualt_NAME # 项目名称
from config import defualt_DataPath # 项目Data文件路径
from config import system_functions # 内置 函数调用表
from config import custom_functions # 自定义 函数调用表

import system.mc as mc