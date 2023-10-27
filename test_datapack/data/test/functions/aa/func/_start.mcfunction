##函数参数初始化
#函数传参赋值
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system data.call_list[-1][0].value
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system data.call_list[-1][{"id":"self"}].value
##函数主体
#表达式调用 (CALL: wrapper())

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system stack_frame append from storage test:system stack_frame[-1]
#函数调用
function test:wrapper/_start
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
#函数定义 (NAME: wrapper)
data modify storage test:system stack_frame[-1].data[{"id":"wrapper"}].value set value "test:aa/func/wrapper/_start"
#表达式调用 (CALL: inner())

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system stack_frame append from storage test:system stack_frame[-1]
#函数调用
function test:inner/_start
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
