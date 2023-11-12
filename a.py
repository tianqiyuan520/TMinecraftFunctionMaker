# from functools import cache
import system.t_algorithm_lib as t_algorithm_lib
import system.mc as mc
# #
# mc.NewFunction('load')
# mc.WriteFunction('load',["say 重载完成222","playsound minecraft:block.anvil.land voice @a ~ ~ ~ 2 2"])
# mc.newTags("load","minecraft",["test:load"],"functions")

@mc.tag("load")
def reload():
    '''数据包重新加载时触发
    '''
    print("重载完成")

# t_algorithm_lib.example(3)

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
# def fib(n)->"int":
#     if n <= 2:
#         return 1
#     else:
#         return fib(n - 1) + fib(n - 2)

# for i in range(1,14):
#     print(fib(i))

# class aa:
#     def test(self) ->"bb":
#         return bb()
# class bb:
#     ...
# a = aa().test()


# class vector:
#     def __init__(self,a,b):
#         self.a = a
#         self.b = b
#     def __add__(self,other)->"vector":
#         return vector(self.a+other.a, self.b+other.b)
#     def __sub__(self,other)->"vector":
#         return vector(self.a-other.a, self.b-other.b)
#     def __mul__(self,other)->"vector":
#         return vector(self.a*other.a, self.b*other.b)
#     def __str__(self) -> str:
#         print(self.a,self.b)
#         return "233"
# v1 = vector(2,10)
# v2 = vector(4,5)
# v3 = ((v2 - v1)+v1) * v2 *v2
# print(v3)


# class aa:
#     def __init__(self) -> None:
#         self.x = 0
#     def b(self)->"aa":
#         ...

# a = aa()
# x = a.b().b()

##
# def inner():
#     print(6)
# inner()
# #闭包
# def func(x,b=4):
#     def wrapper(y):
#         def inner(z):
#             print(b,x,y,z)
#         return inner
#     return wrapper

# x = func(1,b="数据:")(2)("👌")


# x = {a:3}
# args=arguments(posonlyargs=[], args=[arg(arg='x'), arg(arg='b')], kwonlyargs=[], kw_defaults=[], defaults=[])

# 数组
# 壹 = 1
# a = [2,"612",[壹,["❤"+"❤"]]]
# print(a[2][壹][0])

# 类中的闭包函数
# def inner():
#     inner()

# def wrapper():
#     print(6)

# class aa:
#     def func(self):
#         wrapper()
#         def wrapper():
#             def inner():
#                 while 1==1:
#                     wrapper()
#             inner()
#         inner()
#     def func2(self):
#         ...

# 字典
# m = "abc"
# a = {
#     "abc":"def",
#     "key":{"name":"1"},
#     "x":[0,["k"],{"name2":"2333"}]
#     }
# def get(arg):
#     return "def"

# print(a["x"][2]["name2"])
# a["x"][2]=m # test change
# print(a["x"][2])
# funcValue = get("abc") # test call Function
# print(funcValue)
# print(a["key"]['name'],a['x'][1][0])

# x = "32"
# a = {"x":[{"abc":"test"}]}
# a['x'][0]["abc"] = [2,3]
# print(a['x'][0]["abc"][1])

# a = {"name":"1"}
# def get2(arg:"str"="3"): #使用切片时，若该变量为键名，需注明类型为字符串
#     # arg:"str" = arg #使用切片时，若该变量为键名，需注明类型为字符串
#     return a[arg]
# print(get2("name"))

# # get方法
# a = {"name":"123"}
# print(a.get("name"))