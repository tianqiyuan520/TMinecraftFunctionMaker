#
function test:aa/fib/condition_1/if/1
execute if score #test.system.c.1.1 input matches 1 run scoreboard players set #test.system.c.1.pass input 1
