import os
import hashlib

def fileHash(filename):
    md5 = hashlib.md5()
    f = open(filename, 'rb')
    md5.update(f.read())
    f.close()
    return md5.hexdigest()

def ensurePathExists(filename):
    path = filePath(filename)
    if not os.path.exists(path):
        os.makedirs(path)

def filePath(filename):
    "get the part that isn't the title"
    return os.sep.join(os.path.normpath(filename).split(os.sep)[:-1])

class DummyStorage():
    """
    This is the interface that storage backends use.
    """

    def __init__(self):
        """
        called once to initialize storage
        """
        pass

    def store(self, inFilename, file_id, reducedRedundancy=False):
        """
        stores inFilename from local hard drive to some data storage
            with a string identifier of file_id.
        if reducedRedundancy is True, the storage engine has permission
            be less safe with the data.
        """
        pass

    def retrieve(self, file_id, outFilename):
        """
        retrieves file identified by file_id and saves it to outFilename
        """
        pass

    def delete(self, file_id):
        """
        deletes the file identified by file_id from storage
        """
        pass
