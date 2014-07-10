line = "abc def ghi; jkl mno,pqr,    foo"

line.find("ghi") # 8
line.find(",") # 20 finds first occurence
line.find("X") # -1 not found
line.find("ef", 3, -1) # 5 first occurence in range but index of full string