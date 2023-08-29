execute if data storage test:system main_tree[-1].is_continue run scoreboard players reset #test:system.stack.end input
execute if data storage test:system main_tree[-1].is_continue run data remove storage test:system main_tree[-1].is_continue
execute unless score #test:system.stack.end input matches 1 run function test:myfunc/while_1/condition/_start
##while 主程序
execute unless score #test:system.stack.end input matches 1 run execute if score #test.sys.c.1.pass input matches 1 run function test:myfunc/while_1/main
