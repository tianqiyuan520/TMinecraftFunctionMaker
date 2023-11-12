function test:_init

#函数定义 (NAME: reload)
data modify storage test:system stack_frame[-1].data[{"id":"reload"}].value set value "test:reload/_start"
#赋值 a = {'name': '123'}
data modify storage test:system data.dict_handlerK set value [{}]
data modify storage test:system data.dict_handlerV set value {}
data modify storage test:system data.dict_handlerK[-1].'name'.value set value "123"
data modify storage test:system stack_frame[-1].data[{"id":"a"}].type set value "dict"
data modify storage test:system stack_frame[-1].data[{"id":"a"}].value set from storage test:system data.dict_handlerK[-1]
#表达式调用 (CALL: print(a.get('name')))

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []

##函数调用_begin (自定义类的方法调用)
#参数处理.函数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append value {"value": "name", "id": "None"}
data modify storage test:system stack_frame append from storage test:system stack_frame[-1]
data modify storage test:system stack_frame[-1].dync.arg0 set from storage test:system data.call_list[-1][-1].value
    ##动态命令调用
function test:__main__/dync_0/_start with storage test:system stack_frame[-1].dync
    ##动态命令调用end
data modify storage test:system stack_frame[-2].return append value {"value": 0}
data modify storage test:system stack_frame[-2].return[-1].value set from storage test:system data.Subscript
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
data remove storage test:system data.call_list[-1]
data modify storage test:system data.call_list[-1] append value {"value": 0, "id": "None"}
data modify storage test:system data.call_list[-1][-1].value set from storage test:system stack_frame[-1].return[-1].value
data modify storage test:system stack_frame append from storage test:system stack_frame[-1]
#内置函数/类实例化调用
#函数传参赋值
#自定义函数调用
tellraw @a [{"nbt":"data.call_list[-1][0].value","storage":"test:system"}]
##函数调用_end
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
