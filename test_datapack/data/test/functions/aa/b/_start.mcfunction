##函数参数初始化
##函数主体
##函数返回值处理_bengin
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system stack_frame[-2].return append value {"value":0}
data modify storage test:system stack_frame[-2].return[-1].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
scoreboard players set #test:system.stack.end input 1

    ##终止
    return 1
    ##
##函数返回值处理_end
##函数结尾
