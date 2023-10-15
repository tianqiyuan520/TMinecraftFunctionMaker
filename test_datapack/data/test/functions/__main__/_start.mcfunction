function test:_init

data modify storage test:system data.list_handler set value []
data modify storage test:system data.list_handler append value {"value": []}
data modify storage test:system data.list_handler[-1].value append value {"value": 1}
data modify storage test:system data.list_handler[-1].value append value {"value": 2}
data modify storage test:system data.list_handler append value {"value": 3}
data modify storage test:system stack_frame[-1].data[{"id":"b"}].type set value "list"
data modify storage test:system stack_frame[-1].data[{"id":"b"}].value set from storage test:system data.list_handler
data modify storage test:system stack_frame[-1].dync.arg1 set value 0
data modify storage test:system stack_frame[-1].dync.arg0 set value 0
    ##动态命令调用
function test:__main__/dync_0/_start with storage test:system stack_frame[-1].dync
    ##动态命令调用end
data modify storage test:system stack_frame[-1].data[{"id":"c"}].type set value "int"
data modify storage test:system stack_frame[-1].data[{"id":"c"}].value set from storage test:system data.Subscript
