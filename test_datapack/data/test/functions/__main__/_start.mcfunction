function test:_init

#函数定义 (NAME: reload)
data modify storage test:system stack_frame[-1].data[{"id":"reload"}].value set value "test:reload/_start"
