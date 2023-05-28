import os
folder = os.path.exists("a/t.txt")
if not folder:
    os.makedirs("a/t.txt")