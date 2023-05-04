# imports - module imports
from candis.ios.cdata import CData

def read(path, *args, **kwargs):
    return CData.load(path)
