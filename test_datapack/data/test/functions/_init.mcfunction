scoreboard objectives add input dummy
scoreboard objectives add input2 dummy
scoreboard players reset * input2
#初始化栈
data modify storage test:system stack_frame set value [{"data":[],"return":[],"boolOPS":[],"boolResult":[],"for_list":[],"dync":{}}]
data modify storage test:system data set value {"exp_operation":[],"list_handler":[],"dict_handler":[],"call_list":[],"Subscript":""}
#初始化堆
data modify storage test:system heap set value []
