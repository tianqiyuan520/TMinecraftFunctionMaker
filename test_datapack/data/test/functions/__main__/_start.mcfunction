function test:_init

#函数定义 (NAME: reload)
data modify storage test:system stack_frame[-1].data[{"id":"reload"}].value set value "test:reload/_start"
#函数定义 (NAME: inner)
data modify storage test:system stack_frame[-1].data[{"id":"inner"}].value set value "test:inner/_start"
#函数定义 (NAME: wrapper)
data modify storage test:system stack_frame[-1].data[{"id":"wrapper"}].value set value "test:wrapper/_start"
#类定义 (NAME: aa)aa
#赋值 a = aa()

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system stack_frame append from storage test:system stack_frame[-1]
#内置函数/类实例化调用
#类方法调用.参数处理
data modify storage test:system data.call_list[-1] prepend value {"value": [], "id": "self"}
data modify storage test:system stack_frame[-2].return append value {"value":0}
data modify storage test:system stack_frame[-2].return[-1].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
data modify storage test:system stack_frame[-1].data[{"id":"a"}].type set value "aa"
data modify storage test:system stack_frame[-1].data[{"id":"a"}].value set from storage test:system stack_frame[-1].return[-1].value
#表达式调用 (CALL: a.func())

##函数调用_begin (自定义类的方法调用)
#参数处理.函数处理
data modify storage test:system data.call_list append value []
data modify storage test:system stack_frame append from storage test:system stack_frame[-1]
#函数参数赋值
data modify storage test:system data.call_list[-1] prepend value {"value": [], "id": "self"}
data modify storage test:system data.call_list[-1][0] set from storage test:system stack_frame[-1].data[{"id":"a"}]

#类方法调用
function test:aa/func/_start
data modify storage test:system stack_frame[-1].data[{"id":"a"}].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system data.call_list[-1]
