__version__='0.1'

__all__ = ['initialize','definitions']

prog__init__='(fripipe.__init__) '

from initialize import * 

# Now tries to import all private data
try:
    from fripipe.private.passwords import Database,MeteoFrance
except:
    print prog__init__+'*** Warning: unable to import fripipe.private.passwords'
    pass
try:
    from fripipe.private.privatefiles import fri_station_file,friponkernel
except:
    print prog__init__+'*** Warning: unable to import private.privatefiles'
    pass

