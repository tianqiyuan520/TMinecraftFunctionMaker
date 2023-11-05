##TMCFM编译器
##将类似python的语言转化为Minecraft数据包
# -*- encoding: utf-8 -*-
'''
@File    :   main.py
@Time    :   2023/5/13
@Author  :   tianqiyuan520
'''

import ast
from TMCFM import TMCFM
from read_config import read_json
import platform
import time
if __name__ == "__main__":

    try:
        ## play music
        # from pydub import AudioSegment
        # from pydub.playback import play
        # import random
        # rand = random.choice([1,2])
        # song = AudioSegment.from_file(f"sounds/smithing_table{rand}.mp3", format="mp3")
        # play(song)
        ...
    except:
        # print("Missing playsound\npip install pydub\npip install simpleaudio")
        ...

    #open file
    content = ""
    cfg = read_json.read('config.json')['config']
    #
    with open(cfg["InputFile"],'r',encoding='utf-8') as f:
        # content = f.read().split('\n')
        content = f.read()
    # content = input('>>> ')
    T1 = time.perf_counter()
    
    #ast show
    code_ = ast.parse(content)
    print(ast.dump(code_))
    cfg = read_json.read('config.json')['config']
    for i in range(len(cfg["path"])):
        comp = TMCFM(content,i)
        comp.main()

    T2 =time.perf_counter()
    print('success runTime:%sms' % ((T2 - T1)*1000))
    # input(">>> ")
