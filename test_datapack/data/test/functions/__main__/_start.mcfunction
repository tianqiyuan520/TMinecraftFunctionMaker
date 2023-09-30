scoreboard players reset * input2
#初始化栈
data modify storage test:system stack_frame set value [{"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}]

##    调用函数
#参数处理
data modify storage test:system stack_frame[-1].call_list append value []
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#内置函数or类实例化调用
#类方法调用.参数处理
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set value []
#类方法调用.初始化
function test:aa/__init__/_start
data modify storage test:system stack_frame[-2].return append value {"value":0}
data modify storage test:system stack_frame[-2].return[-1].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system stack_frame[-1].call_list[-1]
data modify storage test:system stack_frame[-1].data[{"id":"a"}].type set value "aa"
data modify storage test:system stack_frame[-1].data[{"id":"a"}].value set from storage test:system stack_frame[-1].return[-1].value
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}

##函数调用_begin (自定义类的方法调用)
#参数处理.函数处理
data modify storage test:system stack_frame[-1].call_list append value []
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
data modify storage test:system stack_frame[-1].call_list set from storage test:system stack_frame[-2].call_list
#参数处理.赋值
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system stack_frame[-1].data[{"id":"a"}].value

#类方法调用
function test:aa/b/_start
data modify storage test:system stack_frame[-1].data[{"id":"a"}].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system stack_frame[-1].call_list[-1]
data modify storage test:system stack_frame[-1].return append value {"value": 0, "type": "num"}
data modify storage test:system stack_frame[-1].return[-1].value set from storage test:system stack_frame[-1].return[-2].value[{"id":"x"}].value
data remove storage test:system stack_frame[-1].call_list[-1]
data modify storage test:system stack_frame[-1].data[{"id":"bb"}].type set value "aa"
data modify storage test:system stack_frame[-1].data[{"id":"bb"}].value set from storage test:system stack_frame[-1].return[-1].value
