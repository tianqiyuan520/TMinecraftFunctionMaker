##函数参数初始化
##函数主体
data modify storage test:system main_tree[-1].data[{"id":"i"}].value set value 0
     ##while_begin   
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data set from storage test:system main_tree[-2].data
execute unless score #test:system.stack.end input matches 1 run function test:myfunc/while_1/_start
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-2].data set from storage test:system main_tree[-1].data
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
     ##while_end     
##函数结尾
