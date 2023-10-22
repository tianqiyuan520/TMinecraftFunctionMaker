function test:_init

#函数定义 (NAME: reload)
data modify storage test:system stack_frame[-1].data[{"id":"reload"}].value set value "test:reload/_start"
#函数定义 (NAME: inner)
data modify storage test:system stack_frame[-1].data[{"id":"inner"}].value set value "test:inner/_start"
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
#函数定义 (NAME: func)
data modify storage test:system stack_frame[-1].data[{"id":"func"}].value set value "test:func/_start"
#赋值 x = func(1, b='数据:')(2)('👌')

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append value {"value": 1, "id": "None"}
data modify storage test:system data.call_list[-1] append value {"value": "数据:", "id": "b"}
data modify storage test:system stack_frame append from storage test:system stack_frame[-1]
#函数调用
function test:func/_start
data modify storage test:system temp set from storage test:system stack_frame[-1]
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
data modify storage test:system data.call_list[-1][-1].value set from storage test:system stack_frame[-1].return[-1].value

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append value {"value": 2, "id": "None"}
data modify storage test:system stack_frame append from storage test:system temp
#函数调用
data modify storage test:system stack_frame[-1].dync.arg0 set from storage test:system stack_frame[-2].return[-1].value
function test:__main__/dync_0/_start with storage test:system stack_frame[-1].dync
data modify storage test:system temp set from storage test:system stack_frame[-1]
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
data modify storage test:system data.call_list[-1][-1].value set from storage test:system stack_frame[-1].return[-1].value

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append value {"value": "👌", "id": "None"}
data modify storage test:system stack_frame append from storage test:system temp
#函数调用
data modify storage test:system stack_frame[-1].dync.arg0 set from storage test:system stack_frame[-2].return[-1].value
function test:__main__/dync_1/_start with storage test:system stack_frame[-1].dync
data modify storage test:system temp set from storage test:system stack_frame[-1]
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
data modify storage test:system stack_frame[-1].data[{"id":"x"}].type set value "None"
data modify storage test:system stack_frame[-1].data[{"id":"x"}].value set from storage test:system stack_frame[-1].return[-1].value
