# from functools import cache
import system.t_algorithm_lib as t_algorithm_lib
import system.mc as mc
# #
# mc.NewFunction('load')
# mc.WriteFunction('load',["say 重载完成222","playsound minecraft:block.anvil.land voice @a ~ ~ ~ 2 2"])
# mc.newTags("load","minecraft",["test:load"],"functions")

@mc.tag("load")
def reload():
    print("重载完成")

# mc.newTags("tick","minecraft",["test:tick"],"functions")

# class aa:
#     def __init__(self,*args) -> None:
#         pass
#     def b(self,x)->"aa":
#         self.x = x
#         return self

#     def fib(self,n)->"int":
#         if n <= 2:
#             return 1
#         else:
#             return self.fib(n - 1) + self.fib(n - 2)
# class test(aa):
#     def __init__(self,x=3)->str:
#         self.xx = 1
#         # self.xx.xxx = 1
#     def a(self,x):
#         print(x)
#     def b(self,x):
#         print('*  ',x)
#         return x
#     def c(self):
#         return self

# a= test(22)
# x = a.fib(a.b(10)+5)
# print(x)

# @mc.event.ifEntytPosDownZero("tianqiyuan520")
# def test_aa():
    # print("aaa",1+1)


# a = aa("aaa")
# a.b(1).b(2)
# print(a.x)

# if(1 and (22==22 or 33==23)):
    # if(1 and 1):
        # ...
    # ...
# a = 1 and 3
# print(a)
# a = (1==1 and 1==1)

# def test():
#     i = 0
#     while i < 10:
#         mc.run(['say ',str(i)])
#         i += 1
# test()


# @mc.cache
# def aa():
#     return 3

# class aa:
#     def test(self) ->"bb":
#         return bb()
# class bb:
#     ...
# a = aa().test()