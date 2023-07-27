##函数参数初始化
execute unless score #test:system.stack.end input matches 1 run execute unless data storage test:system main_tree[-1].data[{"id":"x"}] run data modify storage test:system main_tree[-1].data[{"id":"x"}].value set value 3
##函数主体
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system main_tree[-1].data[{"id":"self"}].value[{"id":"xx"}].value set value 1
##函数结尾
