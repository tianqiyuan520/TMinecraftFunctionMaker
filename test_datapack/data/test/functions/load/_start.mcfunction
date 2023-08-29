#初始化栈
data modify storage test:system main_tree set value [{"data":[],"return":[],"exp_operation":[],"boolOPS":[],"boolResult":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}]

##    调用函数
#参数处理
data modify storage test:system main_tree[-1].call_list append value []
#新建栈
data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[]}
#参数处理.赋值
#函数调用
function test:myfunc/_start
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system main_tree[-1].call_list[-1]
