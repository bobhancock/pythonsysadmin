def md5sum_file(filename):
    """ Return the md5 sum for a file.
    
    This can be used to compare two file to determine if they are identical.
    """
    import hashlib
    
    infile = open(filename, 'rb')
    content = infile.read()
    infile.close()
    m = hashlib.md5() 
    m.update(content)
    md5 = m.hexdigest() # now the md5 variable contains the MD5 sum
    
    return md5