function test:_init

#函数定义 (NAME: reload)
data modify storage test:system stack_frame[-1].data[{"id":"reload"}].value set value "test:reload/_start"
#赋值 m = 'abc'
data modify storage test:system stack_frame[-1].data[{"id":"m"}].value set value "abc"
data modify storage test:system stack_frame[-1].data[{"id":"m"}].type set value "str"
#赋值 a = {'abc': m, 'key': {'name': '1'}, 'x': [0, ['k']]}
data modify storage test:system data.dict_handlerK set value [{}]
data modify storage test:system data.dict_handlerV set value {}
data modify storage test:system data.dict_handlerK[-1].'abc' set from storage test:system stack_frame[-1].data[{"id":"m"}].value
#value: 
data modify storage test:system data.dict_handlerK append value {}
data modify storage test:system data.dict_handlerK[-1].'name' set value "1"
data modify storage test:system data.dict_handlerV set from storage test:system data.dict_handlerK[-1]
data remove storage test:system data.dict_handlerK[-1]
#key: 
data modify storage test:system data.dict_handlerK[-1].'key' set from storage test:system data.dict_handlerV
#value: 
data modify storage test:system data.list_handler set value []
data modify storage test:system data.list_handler set value [{"value": 0, "type": "int"}]
data modify storage test:system data.list_handler append value {"value": []}
data modify storage test:system data.list_handler[-1].value set value [{"value": "k", "type": "str"}]
data modify storage test:system data.dict_handlerV set from storage test:system data.list_handler
#key: 
data modify storage test:system data.dict_handlerK[-1].'x' set from storage test:system data.dict_handlerV
data modify storage test:system stack_frame[-1].data[{"id":"a"}].type set value "dict"
data modify storage test:system stack_frame[-1].data[{"id":"a"}].value set from storage test:system data.dict_handlerK[-1]
#赋值 b = a[m]
data modify storage test:system stack_frame[-1].dync.arg0 set from storage test:system stack_frame[-1].data[{"id":"m"}].value
    ##动态命令调用
function test:__main__/dync_0/_start with storage test:system stack_frame[-1].dync
    ##动态命令调用end
data modify storage test:system stack_frame[-1].data[{"id":"b"}].type set value "None"
data modify storage test:system stack_frame[-1].data[{"id":"b"}].value set from storage test:system data.Subscript
#表达式调用 (CALL: print(b, a['key']['name'], a['x'][1][0]))

##    调用函数
#参数处理
data modify storage test:system data.call_list append value []
data modify storage test:system data.call_list[-1] append from storage test:system stack_frame[-1].data[{"id":"b"}]
data modify storage test:system stack_frame[-1].dync.arg1 set value "key"
data modify storage test:system stack_frame[-1].dync.arg0 set value "name"
    ##动态命令调用
function test:__main__/dync_1/_start with storage test:system stack_frame[-1].dync
    ##动态命令调用end
data modify storage test:system data.call_list[-1] append value {"value": 0, "id": "None"}
data modify storage test:system data.call_list[-1][-1].value set from storage test:system data.Subscript
data modify storage test:system stack_frame[-1].dync.arg2 set value "x"
data modify storage test:system stack_frame[-1].dync.arg1 set value 1
data modify storage test:system stack_frame[-1].dync.arg0 set value 0
    ##动态命令调用
function test:__main__/dync_2/_start with storage test:system stack_frame[-1].dync
    ##动态命令调用end
data modify storage test:system data.call_list[-1] append value {"value": 0, "id": "None"}
data modify storage test:system data.call_list[-1][-1].value set from storage test:system data.Subscript
data modify storage test:system stack_frame append from storage test:system stack_frame[-1]
#内置函数/类实例化调用
#函数传参赋值
#自定义函数调用
tellraw @a [{"nbt":"data.call_list[-1][0].value","storage":"test:system"}," ",{"nbt":"data.call_list[-1][1].value","storage":"test:system"}," ",{"nbt":"data.call_list[-1][2].value","storage":"test:system"}]
##函数调用_end
data remove storage test:system stack_frame[-1]
scoreboard players reset #test:system.stack.end input
##  调用结束
data remove storage test:system data.call_list[-1]
