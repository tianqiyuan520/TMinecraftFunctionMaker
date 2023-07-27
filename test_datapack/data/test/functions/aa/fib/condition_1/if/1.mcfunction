execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].boolOPS append value {"value": 0}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].boolOPS[-1].value set from storage test:system main_tree[-1].data[{"id":"n"}].value
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].boolOPS append value {"value": 2}
scoreboard players reset #test.sys.c.1.1 input
execute unless score #test:system.stack.end input matches 1 run execute store result score #test.system.temp1 input run data get storage test:system main_tree[-1].boolOPS[-2].value 1000
execute store result score #test.system.temp2 input run data get storage test:system main_tree[-1].boolOPS[-1].value 1000
execute if score #test.system.temp1 input <= #test.system.temp2 input run scoreboard players set #test.sys.c.1.1 input 1
