#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data set from storage test:system main_tree[-2].data
execute unless score #test:system.stack.end input matches 1 run function test:myfunc/condition_1/if/1
scoreboard players set #test.sys.c.1.pass input 0
execute if score #test.sys.c.1.1 input matches 1 run scoreboard players set #test.sys.c.1.pass input 1
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
