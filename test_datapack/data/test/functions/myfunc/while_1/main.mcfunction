execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list append value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1] append value {"value": "summon creeper ", "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1] append value {"value": 0, "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1][-1].value set from storage test:system main_tree[-1].data[{"id":"i"}].value
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].call_list[-1] append value {"value": " 0 0", "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].dync set value {}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].dync.arg0 set from storage test:system main_tree[-1].call_list[-1][0].value
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].dync.arg1 set from storage test:system main_tree[-1].call_list[-1][1].value
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].dync.arg2 set from storage test:system main_tree[-1].call_list[-1][2].value
execute unless score #test:system.stack.end input matches 1 run function test:myfunc/dync_0/_start with storage test:system main_tree[-1].dync
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].dync set value {}
data remove storage test:system main_tree[-1].call_list[-1]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].exp_operation[-1] append from storage test:system main_tree[-1].data[{"id":"i"}]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].exp_operation append value {"value":1,"type":"num"}
execute unless score #test:system.stack.end input matches 1 run execute store result score #test.system.temp1 input run data get storage test:system main_tree[-1].exp_operation[-2].value 1000
execute store result score #test.system.temp2 input run data get storage test:system main_tree[-1].exp_operation[-1].value 1000
execute unless score #test:system.stack.end input matches 1 run execute store result storage test:system main_tree[-1].exp_operation[-1].value double 0.001 run scoreboard players operation #test.system.temp1 input += #test.system.temp2 input
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1].exp_operation[-2]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data[{"id":"i"}].value set from storage test:system main_tree[-1].exp_operation[-1].value
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1].exp_operation[-1]
function test:myfunc/while_1/_start
