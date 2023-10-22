import ast

x = 'a = 1'
print(ast.unparse(ast.parse(x)))