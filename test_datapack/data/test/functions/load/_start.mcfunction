scoreboard objectives add input dummy
#初始化栈
execute unless data storage test:system main_tree[-1].is_end run data modify storage test:system main_tree set value [{"data":[],"return":[],"type":"","exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[]}]
execute unless data storage test:system main_tree[-1].is_end run data modify storage test:system main_tree[-1].return append value {"value": 0}
execute store result storage test:system main_tree[-1].return[-1].value double 1.0 run say hello world
execute unless data storage test:system main_tree[-1].is_end run data modify storage test:system main_tree[-1].data[{"id":"a"}].value set from storage test:system main_tree[-1].return[-1].value
