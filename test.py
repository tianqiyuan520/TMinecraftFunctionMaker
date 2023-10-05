import copy


a = {"value": [1,2,3]}
b = a.copy()
c = copy.deepcopy(a)
print(a,b,c)
a["value"].append(4)
print(a,b,c)

