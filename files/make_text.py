""" Write a text file with test text. """
fh = open("./mytext.txt", "w")
for i in range(100):
    fh.write(str(i)+","+"I am test text.\n")
    
fh.close()    