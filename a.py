import system.t_algorithm_lib as t_algorithm_lib
import system.mc as mc
##
mc.NewFunction('load')
mc.WriteFunction('load',["say 重载完成1","playsound minecraft:entity.player.levelup voice @a ~ ~ ~ 1 2"])
mc.newTags("load","minecraft",["test:load"],"functions")
##

# a=mc.MCEntity("pig")
# a.get_data("UUID")
# print(a)

x = t_algorithm_lib.cos(0)

a = [3,[x]][1][0]

print(a)
