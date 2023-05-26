# TMinecraftFunctionMaker

a compiler that compiles python code into Minecraft datapack functions

## How to use

### First

you should create a config file (path:"~\config.json")

path: the path where the datapack is

name: the Namespace of datapack

pack_format: the version of datapack

description: the description of datapack

scoreboard_objective: the default scoreboard objective

### Second

create your python code

for example:

write this code in "a.py"

```python
a=1
print(1)
```

then run the "main.py"

If everything goes successfully,there will be your compiled datapack in your custom path

### Finally

put this datapack in your game, then run /reload
wait for reloading

then run /function {yourNameSpace}:load/_start

## extra

### the function of python will be a folder in datapck file

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

### the rule of compiling

Now supports basic grammar (such as Assign, Operation, BoolOperation, FunctionDef, for loop, while loop, return .etc)

But now not support inner python function(or class) and other libraries

Some function should be used in other ways.

Compiling them with the support of other datapack( some function library , such as my datapack "TAlgorithmLibrary" ) is necessary

## theory

Use python ast library to translate the python code into ast.

Then walks through the ast and build Mcfunction according to the specific ast node name.

The most important thing is to have stack thoughts