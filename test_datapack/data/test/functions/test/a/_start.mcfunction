##函数参数初始化
##函数主体

##函数调用_begin
#参数处理.函数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list append value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1] append value {"value": 0, "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1][-1].value set from storage test:system main_tree[-1].data[{"id":"x"}].value
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list set from storage test:system main_tree[-2].call_list
#参数处理.赋值
#自定义函数调用
tellraw @a [{"nbt":"main_tree[-1].call_list[-1][0].value","storage":"test:system"}]
##函数调用_end
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1].call_list[-1]
##函数结尾
