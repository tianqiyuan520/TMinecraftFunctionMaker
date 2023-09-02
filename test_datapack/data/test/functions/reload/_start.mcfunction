#数据包重新加载时触发
#    
##函数参数初始化
##函数主体
data remove storage test:system main_tree[-1].call_list[-1]

##    调用函数
#参数处理
data modify storage test:system main_tree[-1].call_list append value []
data modify storage test:system main_tree[-1].call_list[-1] append value {"value": "重载完成", "id": "None"}
#新建栈
data modify storage test:system main_tree append value {"data":[],"return":[],"exp_operation":[],"boolOPS":[],"for_list":[],"call_list":[],"call_list_":[],"list_handler":[],"dync":{}}
data modify storage test:system main_tree[-1].call_list set from storage test:system main_tree[-2].call_list
#内置函数or类实例化调用
#参数处理.赋值
#自定义函数调用
tellraw @a [{"nbt":"main_tree[-1].call_list[-1][0].value","storage":"test:system"}]
##函数调用_end
data remove storage test:system main_tree[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system main_tree[-1].call_list[-1]
##函数返回值处理_bengin
data modify storage test:system main_tree[-2].return append value {"value":"None"}
scoreboard players set #test:system.stack.end input 1

    ##终止
    return 1
    ##
##函数返回值处理_end
##函数结尾
