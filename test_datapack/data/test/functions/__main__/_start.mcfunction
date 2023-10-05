scoreboard players reset * input2
#初始化栈与堆
data modify storage test:system stack_frame set value [{"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}]
data modify storage test:system data set value {"exp_operation":[],"list_handler":[],"call_list":[],"Subscript":""}
data modify storage test:system heap set value []

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append value {"value": 2, "id": "None"}
data modify storage test:system data.call_list[-1] append value {"value": 10, "id": "None"}
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#内置函数or类实例化调用
#类方法调用.参数处理
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set value []
data modify storage test:system stack_frame[-1].data[{"id":"a"}].value set from storage test:system data.call_list[-1][0].value
data modify storage test:system stack_frame[-1].data[{"id":"b"}].value set from storage test:system data.call_list[-1][1].value
#类方法调用.初始化
function test:vector/__init__/_start
data modify storage test:system stack_frame[-2].return append value {"value":0}
data modify storage test:system stack_frame[-2].return[-1].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
data modify storage test:system stack_frame[-1].data[{"id":"v1"}].type set value "vector"
data modify storage test:system stack_frame[-1].data[{"id":"v1"}].value set from storage test:system stack_frame[-1].return[-1].value

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append value {"value": 4, "id": "None"}
data modify storage test:system data.call_list[-1] append value {"value": 5, "id": "None"}
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#内置函数or类实例化调用
#类方法调用.参数处理
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set value []
data modify storage test:system stack_frame[-1].data[{"id":"a"}].value set from storage test:system data.call_list[-1][0].value
data modify storage test:system stack_frame[-1].data[{"id":"b"}].value set from storage test:system data.call_list[-1][1].value
#类方法调用.初始化
function test:vector/__init__/_start
data modify storage test:system stack_frame[-2].return append value {"value":0}
data modify storage test:system stack_frame[-2].return[-1].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
data modify storage test:system stack_frame[-1].data[{"id":"v2"}].type set value "vector"
data modify storage test:system stack_frame[-1].data[{"id":"v2"}].value set from storage test:system stack_frame[-1].return[-1].value
data modify storage test:system data.exp_operation append from storage test:system stack_frame[-1].data[{"id":"v2"}]
data modify storage test:system data.exp_operation append from storage test:system stack_frame[-1].data[{"id":"v1"}]
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append from storage test:system data.exp_operation[-1]
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#魔术方法-参数处理.赋值
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system stack_frame[-2].exp_operation[-2].value
data modify storage test:system stack_frame[-1].data[{"id":"other"}].value set from storage test:system data.call_list[-1][0].value

#魔术方法-调用
function test:vector/__sub__/_start
data modify storage test:system stack_frame[-2].exp_operation[-2].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system data.call_list[-1]
data modify storage test:system data.exp_operation[-1] set from storage test:system stack_frame[-1].return[-1]
data remove storage test:system data.exp_operation[-2]
data modify storage test:system data.exp_operation append from storage test:system stack_frame[-1].data[{"id":"v1"}]
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append from storage test:system data.exp_operation[-1]
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#魔术方法-参数处理.赋值
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system stack_frame[-2].exp_operation[-2].value
data modify storage test:system stack_frame[-1].data[{"id":"other"}].value set from storage test:system data.call_list[-1][0].value

#魔术方法-调用
function test:vector/__add__/_start
data modify storage test:system stack_frame[-2].exp_operation[-2].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system data.call_list[-1]
data modify storage test:system data.exp_operation[-1] set from storage test:system stack_frame[-1].return[-1]
data remove storage test:system data.exp_operation[-2]
data modify storage test:system data.exp_operation append from storage test:system stack_frame[-1].data[{"id":"v2"}]
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append from storage test:system data.exp_operation[-1]
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#魔术方法-参数处理.赋值
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system stack_frame[-2].exp_operation[-2].value
data modify storage test:system stack_frame[-1].data[{"id":"other"}].value set from storage test:system data.call_list[-1][0].value

#魔术方法-调用
function test:vector/__mul__/_start
data modify storage test:system stack_frame[-2].exp_operation[-2].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system data.call_list[-1]
data modify storage test:system data.exp_operation[-1] set from storage test:system stack_frame[-1].return[-1]
data remove storage test:system data.exp_operation[-2]
data modify storage test:system data.exp_operation append from storage test:system stack_frame[-1].data[{"id":"v2"}]
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append from storage test:system data.exp_operation[-1]
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#魔术方法-参数处理.赋值
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system stack_frame[-2].exp_operation[-2].value
data modify storage test:system stack_frame[-1].data[{"id":"other"}].value set from storage test:system data.call_list[-1][0].value

#魔术方法-调用
function test:vector/__mul__/_start
data modify storage test:system stack_frame[-2].exp_operation[-2].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system data.call_list[-1]
data modify storage test:system data.exp_operation[-1] set from storage test:system stack_frame[-1].return[-1]
data remove storage test:system data.exp_operation[-2]
data modify storage test:system stack_frame[-1].data[{"id":"v3"}].type set value "vector"
data modify storage test:system stack_frame[-1].data[{"id":"v3"}].value set from storage test:system data.exp_operation[-1].value
data remove storage test:system data.exp_operation[-1]

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append from storage test:system stack_frame[-1].data[{"id":"v1"}]
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#内置函数or类实例化调用
#参数处理.赋值
#自定义函数调用
data modify storage test:system data.call_list append value []
#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#魔术方法-参数处理.赋值
data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set from storage test:system data.call_list[-2][0].value

#魔术方法-调用
function test:vector/__str__/_start
data modify storage test:system data.call_list[-2][0].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system data.call_list[-1]
tellraw @a [{"nbt":"stack_frame[-1].return[-1].value","storage":"test:system"}]
##函数调用_end
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
