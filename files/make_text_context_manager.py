""" Defered closing of the file occurs when the with statement terminates."""

with open(".mytext_context_mgr.txt", "w") as fh:
    for i in range(100):
        fh.write(str(i)+","+"I am test text.\n")
    