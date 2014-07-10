import re

line = "abc def ghi; jkl mno,pqr,    foo"
s = re.split(r'[;,\s]\s*', line)

print(s)