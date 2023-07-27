##函数参数初始化
##函数主体
scoreboard players set #test.sys.c.1.pass input 0
scoreboard players set #test.sys.c.1.end input 0
execute unless score #test:system.stack.end input matches 1 run execute if score #test.sys.c.1.pass input matches 0 if score #test.sys.c.1.end input matches 0 run function test:aa/fib/condition_1/if/call
#
execute unless score #test:system.stack.end input matches 1 run execute if score #test.sys.c.1.pass input matches 1 run function test:aa/fib/condition_1/if/main
#
execute unless score #test:system.stack.end input matches 1 run execute if score #test.sys.c.1.pass input matches 0 run function test:aa/fib/condition_1/else/main
##函数结尾
