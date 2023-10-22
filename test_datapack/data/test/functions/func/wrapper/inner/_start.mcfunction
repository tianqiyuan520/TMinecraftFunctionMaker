##函数参数初始化
#函数传参赋值
data modify storage test:system stack_frame[-1].data[{"id":"z"}].value set from storage test:system data.call_list[-1][0].value
data modify storage test:system stack_frame[-1].data[{"id":"z"}].value set from storage test:system data.call_list[-1][{"id":"z"}].value
##函数主体
#表达式调用 (CALL: print(b, x, y, z))

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append from storage test:system stack_frame[-1].data[{"id":"b"}]
data modify storage test:system data.call_list[-1] append from storage test:system stack_frame[-1].data[{"id":"x"}]
data modify storage test:system data.call_list[-1] append from storage test:system stack_frame[-1].data[{"id":"y"}]
data modify storage test:system data.call_list[-1] append from storage test:system stack_frame[-1].data[{"id":"z"}]
data modify storage test:system stack_frame append from storage test:system stack_frame[-1]
#内置函数/类实例化调用
#函数传参赋值
#自定义函数调用
tellraw @a [{"nbt":"data.call_list[-1][0].value","storage":"test:system"}," ",{"nbt":"data.call_list[-1][1].value","storage":"test:system"}," ",{"nbt":"data.call_list[-1][2].value","storage":"test:system"}," ",{"nbt":"data.call_list[-1][3].value","storage":"test:system"}]
##函数调用_end
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
##函数返回值处理_bengin
data modify storage test:system stack_frame[-2].return append value {"value":"None"}
scoreboard players set #test:system.stack.end input 1

    ##终止
    return 1
    ##
##函数返回值处理_end
##函数结尾
