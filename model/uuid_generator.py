# -*- coding: utf-8 -*- 
import uuid
from model.mc_nbt import IntArray

#   0                   1                   2                   3
#     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
#    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#    |                          time_low                             |
#    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#    |       time_mid                |         time_hi_and_version   |
#    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#    |clk_seq_hi_res |  clk_seq_low  |         node (0-1)            |
#    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#    |                         node (2-5)                            |
#    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

def get_uuid()->uuid.UUID:
    return uuid.uuid4()

def get_uuid_LSB(uuid:uuid.UUID) -> list:
    '''高低位获取'''
    return [int64(int(uuid.hex[0:16],16)),int64(int(uuid.hex[16:],16))]

def uuid_to_list(uuid:uuid.UUID) -> IntArray:
    '''UUID 转 Intarray'''
    temp = get_uuid_LSB(uuid)
    Intarray = [int32(temp[0]>>32),int32(temp[0]),int32(temp[1]>>32),int32(temp[1])]
    return IntArray(Intarray)

def list_to_uuid(temp:list) -> list:
    '''Intarray 转 UUID'''
    ## 逆着获取高低位
    # LSB = [temp[0]>>32,temp[2]>>32]
    # return LSB
    return None

def int32(num:int)->int:
    '''int32'''
    if num > 2147483647:
        # 判断圈数奇偶
        if int(num/2147483647)%2 ==0:
            return int(bin(num)[-31:],2)
        else:
            return -2147483648 + int(bin(num)[-31:],2)
    elif num < -2147483648:
        # 判断圈数奇偶
        if int(num/2147483648)%2 ==0:
            return int(bin(num)[-31:],2)*-1
        else:
            return (num%2147483648)
    else:
        return num

def int64(num:int)->int:
    '''int64'''
    if num > 9223372036854775807:
        if int(num/9223372036854775807)%2 ==0:
            return int(bin(num)[-63:],2)
        else:
            return -9223372036854775808 + int(bin(num)[-63:],2)
    elif num < -9223372036854775808:
        if int(num/9223372036854775808)%2 ==0:
            return int(bin(num)[-63:],2)*-1
        else:
            return (num%9223372036854775808)
    else:
        return num
