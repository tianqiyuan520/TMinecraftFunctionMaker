execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data[{"id":"i","temp":1b}].value set from storage test:system main_tree[-1].for_list[0].value
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system main_tree[-1].for_list[0]
