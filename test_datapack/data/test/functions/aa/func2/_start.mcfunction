##函数参数初始化
#函数传参赋值
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system data.call_list[-1][0].value
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system data.call_list[-1][{"id":"self"}].value
##函数主体
#表达式调用 (CALL: ...)
##函数返回值处理_bengin
data modify storage test:system stack_frame[-2].return append value {"value":"None"}
scoreboard players set #test:system.stack.end input 1

    ##终止
    return 1
    ##
##函数返回值处理_end
##函数结尾
