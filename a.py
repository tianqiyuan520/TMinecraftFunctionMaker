# import system.t_algorithm_lib as t_algorithm_lib
# import system.mc as mc
##
# mc.NewFunction('load')
# mc.WriteFunction('load',["say 重载完成222","playsound minecraft:block.anvil.land voice @a ~ ~ ~ 2 2"])
# mc.newTags("load","minecraft",["test:load"],"functions")

class aa:
    def __init__(self,*args) -> None:
        pass
    def b(self,x)->"aa":
        self.x = x
        return self

#     def fib(self,n):
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

a = aa("aaa")
a.b(1).b(2)
print(a.x)

for i in range(1,10,2):
    ...