scoreboard objectives add input dummy
scoreboard objectives add input2 dummy
scoreboard players reset * input2
#初始化栈
data modify storage test:system stack_frame set value [{"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}]
data modify storage test:system data set value {"exp_operation":[],"list_handler":[],"call_list":[],"Subscript":""}
#初始化堆
data modify storage test:system heap set value []
