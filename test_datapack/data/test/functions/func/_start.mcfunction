##函数参数初始化
execute unless data storage test:system stack_frame[-1].data[{"id":"b"}] run data modify storage test:system stack_frame[-1].data[{"id":"b"}].value set value 4
#函数传参赋值
data modify storage test:system stack_frame[-1].data[{"id":"x"}].value set from storage test:system data.call_list[-1][0].value
data modify storage test:system stack_frame[-1].data[{"id":"b"}].value set from storage test:system data.call_list[-1][1].value
data modify storage test:system stack_frame[-1].data[{"id":"x"}].value set from storage test:system data.call_list[-1][{"id":"x"}].value
data modify storage test:system stack_frame[-1].data[{"id":"b"}].value set from storage test:system data.call_list[-1][{"id":"b"}].value
##函数主体
#函数定义 (NAME: wrapper)
data modify storage test:system stack_frame[-1].data[{"id":"wrapper"}].value set value "test:func/wrapper/_start"
#函数返回 (RETURN: return wrapper)
##函数返回值处理_bengin
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system stack_frame[-2].return append value {"value":0}
data modify storage test:system stack_frame[-2].return[-1].value set from storage test:system stack_frame[-1].data[{"id":"wrapper"}].value
scoreboard players set #test:system.stack.end input 1

    ##终止
    return 1
    ##
##函数返回值处理_end
##函数结尾
