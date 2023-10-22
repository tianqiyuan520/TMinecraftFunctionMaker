#新建栈
data modify storage test:system stack_frame append value {"data":[],"return":[],"boolOPS":[],"for_list":[],"dync":{}}
#函数调用
function test:reload/_start
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
