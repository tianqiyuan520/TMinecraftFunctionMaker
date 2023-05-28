scoreboard objectives add input dummy
#初始化栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree set value [{"data":[],"return":[],"type":"","exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"list_handler":[]}]
summon pig ~ ~ ~ {"UUID" : [I; 1047864546, 1340229909, -1798401673, 1669421009]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].return append value {"value" : [I; 1047864546, 1340229909, -1798401673, 1669421009]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data[{"id":"a"}].value set from storage test:system main_tree[-1].return[-1].value
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].return append value {"value": 0}
data modify storage test:system main_tree[-1].return[-1].value set from entity 3e7524e2-cfe2-4915-94ce-9177638157d1 UUID
##函数调用_begin
#参数处理.函数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list append value {"value": 0, "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1].value set from storage test:system main_tree[-1].data[{"id":"a"}].value
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"type":"","exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set from storage test:system main_tree[-2].call_list
#参数处理.赋值
#函数调用
tellraw @a [{"nbt":"main_tree[-1].call_list[0].value","storage":"test:system"}]
##函数调用_end
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].return append value {"value": 0}
execute store result storage test:system main_tree[-1].return[-1].value double 1.0 run tellraw @a [{"text":"33"}]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data[{"id":"a"}].value set from storage test:system main_tree[-1].return[-1].value
##函数调用_begin
#参数处理.函数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list append value {"value": 32, "id": "None"}
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"type":"","exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set from storage test:system main_tree[-2].call_list
#参数处理.赋值
data modify storage t_algorithm_lib:maths trigonometric_functions.input set from storage test:system main_tree[-1].call_list[0].value
#函数调用
function t_algorithm_lib:maths/trigonometric_functions/sin_cos_tan/start
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-2].return append value {"value": 0}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-2].return[-1].value set from storage t_algorithm_lib:maths trigonometric_functions.result.cos
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data[{"id":"x"}].value set from storage test:system main_tree[-1].return[-1].value
##函数调用_begin
#参数处理.函数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list append value {"value": 0, "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1].value set from storage test:system main_tree[-1].data[{"id":"x"}].value
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"type":"","exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set from storage test:system main_tree[-2].call_list
#参数处理.赋值
#函数调用
tellraw @a [{"nbt":"main_tree[-1].call_list[0].value","storage":"test:system"}]
##函数调用_end
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1]
