scoreboard players set #test.sys.c.1.end input 1
##函数返回值处理_bengin
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-2].return append value {"value":1}
scoreboard players set #test:system.stack.end input 1
data modify storage test:system main_tree[-1].is_return set value 1b
##函数返回值处理_end
