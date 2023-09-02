#新建栈
data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
#函数调用
function test:reload/_start
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
