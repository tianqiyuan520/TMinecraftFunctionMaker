# TMinecraftFunctionMaker

a compiler that compiles python code into Minecraft datapack functions

## English

### How to use

#### First

you should create a config file (path:"~\config.json")

path: the path where the datapack is

name: the Namespace of datapack

pack_format: the version of datapack

description: the description of datapack

scoreboard_objective: the default scoreboard objective

#### Second

create your python code

for example:

write this code in "a.py"

```python
a=1
print(1)
```

then run the "main.py"

If everything goes successfully,there will be your compiled datapack in your custom path

#### Finally

put this datapack in your game, then run /reload
wait for reloading

then run /function {yourNameSpace}:load/_start

### extra

#### the function of python will be a folder in datapck file

for examples:

```python
a=1
print(1)
```

the compiled function will be in the path ( {yourNameSpace}:load/_start )

```python
a = 3
def a():
    return b
```

the compiled function will be in the path ( {yourNameSpace}:load/_start and {yourNameSpace}:a/_start )

#### the rule of compiling

Now supports basic grammar (such as Assign, Operation, BoolOperation, FunctionDef, for loop, while loop, return .etc)

But now not support inner python function(or class) and other libraries

Some function should be used in other ways.

Compiling them with the support of other datapack( some function library , such as my datapack "TAlgorithmLibrary" ) is necessary

### theory

Use python ast library to translate the python code into ast.

Then walks through the ast and build Mcfunction according to the specific ast node name.

The most important thing is to have stack thoughts

---

## Chinese

这是一个将 python 代码编译为 Minecraft 数据包函数的编译器

### 如何使用

#### 第一 新建配置文件

使用之前需要在本路径下新建你的配置文件

path: 数据包地址

name: 数据包命名空间

pack_format: 数据包的版本

description: 数据包介绍

scoreboard_objective: 基本的记分板名称

#### 第二 新建python代码

接下来 书写你的 python 代码

在本路径下的 "a.py" 写入

```python
a=1
print(1)
```

然后运行 "main.py"

如果编译没报错的话，将在你设定的路径中生成数据包

#### 第三 运行数据包

将数据包放入游戏，并运行/function {你的命名空间}:load/_start

### 额外的话

#### python代码中的函数会被编译为数据包函数下的文件夹

例如：

```python
a=1
print(1)
```

将会编译在 数据包函数中： {你的命名空间}:load/_start

```python
a = 3
def a():
    return b
```

将会编译在 数据包函数中： {你的命名空间}:load/_start 和 {你的命名空间}:a/_start

其中load就是默认的函数位置

#### 编译规则

现在支持基础语法 (例如 Assign, Operation, BoolOperation, FunctionDef, for loop, while loop, return .etc)

但不支持python的内置函数或类等，或其他第三方库

所以对于这种情况，要特殊处理

编译这些函数时需要其他数据包（尤其是函数库类型的数据包，例如 "T算法库","小豆数学库"...）的支持

### 原理

用了 python 的 ast 库，将python的代码转化为ast

遍历 ast，根据不同的节点，生成对应的mcfunction

最重要的是要具备 堆栈思想

当然可以也先去研究 编译原理(会更困难)
