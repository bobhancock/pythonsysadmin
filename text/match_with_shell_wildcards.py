from fnmatch import fnmatch, fnmatchcase
fnmatch("foo.txt", "*.txt") # True
fnmatch("foo.txt", "?oo.txt") # True
fnmatch("ops32.csv", "ops[0-9]*") # True
fnmatchcase("foo.txt", "*.TXT") # False

