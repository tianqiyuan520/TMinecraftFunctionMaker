#迭代器初始化
execute unless score #test:system.stack.end input matches 1 run function test:load/for_1/iterator/_init
##for 主程序
execute unless score #test:system.stack.end input matches 1 run execute if score #test.system.c.1.pass input matches 1 run function test:load/for_1/main
