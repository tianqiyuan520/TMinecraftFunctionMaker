##函数参数初始化
##函数主体
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value[{"id":"a"}].value set from storage test:system stack_frame[-1].data[{"id":"a"}].value
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value[{"id":"a"}].type set value None
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value[{"id":"b"}].value set from storage test:system stack_frame[-1].data[{"id":"b"}].value
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value[{"id":"b"}].type set value None
##函数返回值处理_bengin
data modify storage test:system stack_frame[-2].return append value {"value":"None"}
scoreboard players set #test:system.stack.end input 1

    ##终止
    return 1
    ##
##函数返回值处理_end
##函数结尾
