import os
from tempfile import TemporaryFile

def is_dir_writeable(directory):
    """ Attempt to write  temp file to the directory, if an exception is
    raised retrun False, otherwise True.
    """
    try:
        destdir = directory
        TemporaryFile('w+b',1, 'tmp', 'tmp', destdir)
        return True
    except OSError:
        return False
    

def not_dirs(listdirs):
    """ From a list of directories return a list of directories that
    are invalid, else return None.
    """
    listD = listdirs
    listResult = []
    for entry in listD:
        if not os.path.isdir(entry):
            listResult.append(entry)

    if len(listResult) > 0:
        return listResult
    else:
        return None


def not_files(listfiles):
    """ From a list of files return a list of files that
    are invalid, else return None.
    """
    listF = listfiles
    listResult = []
    for entry in listF:
        if not os.path.isfile(entry):
            listResult.append(entry)

        if len(listResult) > 0:
            return listResult
        else:
            return None
