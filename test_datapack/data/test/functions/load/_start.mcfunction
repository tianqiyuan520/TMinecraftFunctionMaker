scoreboard objectives add input dummy
#初始化栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree set value [{"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}]
##函数调用_begin
#参数处理.函数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list append value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1] append value {"value": 22, "id": "None"}
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set from storage test:system main_tree[-2].call_list
#参数处理.赋值
data modify storage test:system main_tree[-1].data[{"id":"self"}].value set value []
data modify storage test:system main_tree[-1].data[{"id":"x"}].value set from storage test:system main_tree[-1].call_list[-1][0].value
#函数调用
function test:test/__init__/_start
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-2].return append value {"value":0}
data modify storage test:system main_tree[-2].return[-1].value set from storage test:system main_tree[-1].data[{"id":"self"}].value
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system main_tree[-1].call_list[-1]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data[{"id":"a"}].value set from storage test:system main_tree[-1].return[-1].value
##函数调用_begin
#参数处理.函数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list append value []
##函数调用_begin
#参数处理.函数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list append value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1] append value {"value": 10, "id": "None"}
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set from storage test:system main_tree[-2].call_list
#参数处理.赋值
data modify storage test:system main_tree[-1].data[{"id":"self"}].value set from storage test:system main_tree[-1].data[{"id":"a"}].value
data modify storage test:system main_tree[-1].data[{"id":"x"}].value set from storage test:system main_tree[-1].call_list[-1][0].value
#函数调用
function test:test/b/_start
data modify storage test:system main_tree[-1].data[{"id":"a"}].value set from storage test:system main_tree[-1].data[{"id":"self"}].value
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system main_tree[-1].call_list[-1]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].exp_operation append value {"value": 0, "type": "num"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].exp_operation[-1].value set from storage test:system main_tree[-1].return[-1].value
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].exp_operation append value {"value":5,"type":"num"}
execute unless score #test:system.stack.end input matches 1 run execute store result score #test.system.temp1 input run data get storage test:system main_tree[-1].exp_operation[-2].value 1000
execute store result score #test.system.temp2 input run data get storage test:system main_tree[-1].exp_operation[-1].value 1000
execute unless score #test:system.stack.end input matches 1 run execute store result storage test:system main_tree[-1].exp_operation[-1].value double 0.001 run scoreboard players operation #test.system.temp1 input += #test.system.temp2 input
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1].exp_operation[-2]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1] append value {"value": 0, "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1][-1].value set from storage test:system main_tree[-1].exp_operation[-1].value
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1].exp_operation[-1]
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set from storage test:system main_tree[-2].call_list
#参数处理.赋值
data modify storage test:system main_tree[-1].data[{"id":"self"}].value set from storage test:system main_tree[-1].data[{"id":"a"}].value
data modify storage test:system main_tree[-1].data[{"id":"n"}].value set from storage test:system main_tree[-1].call_list[-1][0].value
#函数调用
function test:aa/fib/_start
data modify storage test:system main_tree[-1].data[{"id":"a"}].value set from storage test:system main_tree[-1].data[{"id":"self"}].value
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system main_tree[-1].call_list[-1]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data[{"id":"x"}].value set from storage test:system main_tree[-1].return[-1].value
##函数调用_begin
#参数处理.函数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list append value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1] append value {"value": 0, "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1][-1].value set from storage test:system main_tree[-1].data[{"id":"x"}].value
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set from storage test:system main_tree[-2].call_list
#参数处理.赋值
#函数调用
tellraw @a [{"nbt":"main_tree[-1].call_list[-1][0].value","storage":"test:system"}]
##函数调用_end
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system main_tree[-1].call_list[-1]
