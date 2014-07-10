""" Read file and skip blank lines. """
with open("./blank_line.txt", "r") as fh:
    for line in fh:
        stripped = line.strip()
        if not stripped:
            continue
        print(stripped.rstrip("\n"))