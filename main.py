##TMCFM编译器
##将类似python的语言转化为Minecraft数据包
'''
author:天起源
'''
import ast
from TMCFM import TMCFM


if __name__ == "__main__":
    #open file
    content = ""
    with open('a.py','r',encoding='utf-8') as f:
        # content = f.read().split('\n')
        content = f.read()
    # content = input('>>> ')

    #ast show
    code_ = ast.parse(content)
    print(ast.dump(code_))

    comp = TMCFM(content)
    # print(content)
    comp.main()
    
    print("success")
    #pip install playsound
    try:
        ## play music
        from pydub import AudioSegment
        from pydub.playback import play
        import random
        rand = random.choice([1,2])
        song = AudioSegment.from_file(f"sounds//smithing_table{rand}.mp3", format="mp3")
        play(song)
    except:
        # print("Missing playsound\npip install pydub\npip install simpleaudio")
        ...