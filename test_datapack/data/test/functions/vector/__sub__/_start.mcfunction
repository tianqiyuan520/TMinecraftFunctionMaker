##函数参数初始化
##函数主体
##函数返回值处理_bengin

##    调用函数
#参数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system data.call_list append value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system data.exp_operation append from storage test:system stack_frame[-1].data[{"id":"self"}].value[{"id":"a"}]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system data.exp_operation append from storage test:system stack_frame[-1].data[{"id":"other"}].value[{"id":"a"}]
execute unless score #test:system.stack.end input matches 1 run execute store result score #test.system.temp1 input run data get storage test:system data.exp_operation[-2].value 1000
execute store result score #test.system.temp2 input run data get storage test:system data.exp_operation[-1].value 1000
execute unless score #test:system.stack.end input matches 1 run execute store result storage test:system data.exp_operation[-1].value double 0.001000000000 run scoreboard players operation #test.system.temp1 input -= #test.system.temp2 input
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system data.exp_operation[-2]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system data.call_list[-1] append value {"value": 0, "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system data.call_list[-1][-1].value set from storage test:system data.exp_operation[-1].value
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system data.exp_operation[-1]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system data.exp_operation append from storage test:system stack_frame[-1].data[{"id":"self"}].value[{"id":"b"}]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system data.exp_operation append from storage test:system stack_frame[-1].data[{"id":"other"}].value[{"id":"b"}]
execute unless score #test:system.stack.end input matches 1 run execute store result score #test.system.temp1 input run data get storage test:system data.exp_operation[-2].value 1000
execute store result score #test.system.temp2 input run data get storage test:system data.exp_operation[-1].value 1000
execute unless score #test:system.stack.end input matches 1 run execute store result storage test:system data.exp_operation[-1].value double 0.001000000000 run scoreboard players operation #test.system.temp1 input -= #test.system.temp2 input
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system data.exp_operation[-2]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system data.call_list[-1] append value {"value": 0, "id": "None"}
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system data.call_list[-1][-1].value set from storage test:system data.exp_operation[-1].value
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system data.exp_operation[-1]
#新建栈
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system stack_frame append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#内置函数or类实例化调用
#类方法调用.参数处理
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system stack_frame[-1].data[{"id":"self"}].value set value []
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system stack_frame[-1].data[{"id":"a"}].value set from storage test:system data.call_list[-1][0].value
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system stack_frame[-1].data[{"id":"b"}].value set from storage test:system data.call_list[-1][1].value
#类方法调用.初始化
function test:vector/__init__/_start
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system stack_frame[-2].return append value {"value":0}
data modify storage test:system stack_frame[-2].return[-1].value set from storage test:system stack_frame[-1].data[{"id":"self"}].value
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
execute unless score #test:system.stack.end input matches 1 run data remove storage test:system data.call_list[-1]
execute unless score #test:system.stack.end input matches 1 run data modify storage test:system stack_frame[-2].return append from storage test:system stack_frame[-1].return[-1]
scoreboard players set #test:system.stack.end input 1

    ##终止
    return 1
    ##
##函数返回值处理_end
##函数结尾
