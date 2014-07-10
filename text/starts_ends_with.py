filename = "foo.txt"
print(filename.endswith("txt")) # True
print(filename.startswith("foo")) # True
print(filename.startswith("bar")) # False
print(filename.startswith( ("bar", "bob", "foo") )) # True
print(filename.startswith("o", 1)) # True
print(filename.startswith("oo", 1, 3)) # True
