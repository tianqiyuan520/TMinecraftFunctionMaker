#
function test:aa/fib/condition_1/if/1
execute if score #test.sys.c.1.1 input matches 1 run scoreboard players set #test.sys.c.1.pass input 1
