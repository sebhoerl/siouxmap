import gzip
import xml.sax
import numpy as np

def open_by_extension(path, mode = 'r'):
    if path[-2:] == 'gz':
        return gzip.open(path, mode)
    else:
        return open(path, mode)

def dtime(time):
    return np.dot(np.array(time.split(':')).astype(np.float), [3600, 60, 1])

def stime(time):
    return '%02d:%02d:%02d' % (time // 3600, (time % 3600) // 60, time % 60)
