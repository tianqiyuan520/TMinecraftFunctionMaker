##函数参数初始化
##函数主体

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append value {"value": 0, "id": "None"}
data modify storage test:system data.call_list[-1][-1].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value[{"id":"a"}].value
data modify storage test:system data.call_list[-1] append value {"value": 0, "id": "None"}
data modify storage test:system data.call_list[-1][-1].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value[{"id":"b"}].value
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#内置函数or类实例化调用
#参数处理.赋值
#自定义函数调用
tellraw @a [{"nbt":"data.call_list[-1][0].value","storage":"test:system"}," ",{"nbt":"data.call_list[-1][1].value","storage":"test:system"}]
##函数调用_end
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
##函数返回值处理_bengin
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system stack_frame[-2].return append value {"value":"233"}
scoreboard players set #test:system.stack.end input 1

    ##终止
    return 1
    ##
##函数返回值处理_end
##函数结尾
