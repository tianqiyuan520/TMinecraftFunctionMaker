# TMinecraftFunctionMaker

![image](封面.png)

a compiler that compiles python code into Minecraft datapack functions

## Chinese

这是一个将 python 代码编译为 Minecraft 数据包函数的编译器

### 如何使用

#### 第一 新建配置文件

使用之前需要在本路径下新建你的配置文件

InputFile: 要编译的代码文件

path: 数据包地址(列表)

name: 数据包命名空间

pack_format: 数据包的版本

description: 数据包介绍

scoreboard_objective: 基本的记分板名称

#### 第二 新建python代码

接下来 书写你的 python 代码

在 编译的代码文件 写入

```python
a=1
print(1)
```

然后运行 "main.py"

如果编译无报错的话，将在你设定的路径中生成数据包

#### 第三 运行数据包

将数据包放入游戏，并运行/function {你的命名空间}:\_\_main\_\_/_start

### 额外的话

#### python代码中的函数会被编译为数据包函数下的文件夹

例如：

```python
a=1
print(1)
```

将会编译在 数据包函数中： {你的命名空间}:\_\_main\_\_/_start

```python
a = 3
def a():
    return b
```

将会编译在 数据包函数中： {你的命名空间}:\_\_main\_\_/_start 和 {你的命名空间}:a/_start

其中\_\_main\_\_就是默认的函数位置

#### 编译规则

现在支持基础语法 (例如 Assign, Operation, BoolOperation, FunctionDef, for loop, while loop, return .etc)

一些数据类型的属性与方法，面向对象，MC动态命令

编译python库函数与第三方函数需要其他数据包（例如 "T算法库","小豆数学库"...）的支持

### 原理

用了 python 的 ast 库，将python的代码转化为ast

遍历 ast，根据不同的节点，生成对应的mcfunction

最重要的是要具备 堆栈思想

当然也可以直接应用 编译原理(会更困难)

---

### 样例

#### 面向对象的斐波那契数列

```python
import system.t_algorithm_lib as t_algorithm_lib
import system.mc as mc
# #
mc.NewFunction('load')
mc.WriteFunction('load',["say 重载完成222","playsound minecraft:block.anvil.land voice @a ~ ~ ~ 2 2"])
mc.newTags("load","minecraft",["test:load"],"functions")
mc.newTags("tick","minecraft",["test:tick"],"functions")

class aa:
    def __init__(self,*args) -> None:
        pass
    def b(self,x)->"aa":
        self.x = x
        return self

    def fib(self,n):
        if n <= 2:
            return 1
        else:
            return self.fib(n - 1) + self.fib(n - 2)
class test(aa):
    def __init__(self,x=3)->str:
        self.xx = 1
        # self.xx.xxx = 1
    def a(self,x):
        print(x)
    def b(self,x):
        print('*  ',x)
        return x
    def c(self):
        return self

a= test(22)
x = a.fib(a.b(10)+5)
print(x)
```

#### 事件监听

```python
@mc.event.ifEntytPosDownZero("@a")
def test_aa():
    print("aaa",1+1)
```

#### 动态命令

```python
import system.mc as mc
def test():
    i = 0
    while i < 10:
        mc.run(['say ',str(i)])
        i+=1
test()
```

#### 数组

```python
数组
壹 = 1
a = [2,"612",[壹,["❤"+"❤"]]]
print(a[2][壹][0])
```

#### 闭包

```python
def inner():
    print(6)
inner()
#闭包
def func(x,b=4):
    def wrapper(y):
        def inner(z):
            print(b,x,y,z)
        return inner
    return wrapper

x = func(1,b="数据:")(2)("👌")
```

#### 字典

```python
## 字典
m = "abc"
a = {
    "abc":"def",
    "key":{"name":"1"},
    "x":[0,["k"],{"name2":"2333"}]
    }
def get(arg):
    return "def"

print(a["x"][2]["name2"])
a["x"][2]=m # test change
print(a["x"][2])
funcValue = get("abc") # test call Function
print(funcValue)
print(a["key"]['name'],a['x'][1][0])

x = "32"
a = {"x":[{"abc":"test"}]}
a['x'][0]["abc"] = [2,3]
print(a['x'][0]["abc"][1])

a = {"name":"1"}
def get2(arg:"str"="3"): #使用切片时，若该变量为键名，需注明类型为字符串
    # arg:"str" = arg #使用切片时，若该变量为键名，需注明类型为字符串
    return a[arg]
print(get2("name"))

#get方法
a = {"name":"123"}
print(a.get("name"))
```

---
