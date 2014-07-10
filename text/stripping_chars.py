line = "Xabc def ghi; jkl Xmno,pqr,    fooXX"
line.strip(";") # removes all Xs at start and end only

line = "    Hello, world!    \n"
line.strip() # 'Hello, world!'
line.rstrip() # '    Hello, world!'
line.lstrip() # 'Hello, world!    \n'
