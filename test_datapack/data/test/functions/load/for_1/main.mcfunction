execute if data storage test:system main_tree[-1].is_continue run scoreboard players reset #test:system.stack.end input
execute if data storage test:system main_tree[-1].is_continue run data remove storage test:system main_tree[-1].is_continue
execute unless score #test:system.stack.end input matches 1 run function test:load/for_1/iterator/_start
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1].call_list[-1]
execute if data storage test:system main_tree[-1].for_list[0] run function test:load/for_1/main
