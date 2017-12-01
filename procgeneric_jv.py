"""
This file is part of FriPipe
the FRIPON reduction pipeline
18/04/2016
Author : FRIPON
Copyright : Observatoire de Paris,
            Universite Paris-Sud,
            CNRS,
            FRIPON
"""

from fripipe import FriPipe
import os, glob
import csv
import datetime
from datetime import timedelta
from initialize import fri_station_file, fri_station_dir

# user defined variables
pipeline_process=[2,3]
start = '20161210'
end = '20161211'


# start of the program
prog="(procgeneric_jv.py) "
ds = datetime.datetime.strptime(start, '%Y%m%d')
de = datetime.datetime.strptime(end, '%Y%m%d')

# read all the FRIPON station names and codes
with open(fri_station_file, 'rb') as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        Id=row[0]
        code=row[1]
        name=row[2]
#        print prog+' now treating station='+name+' code=',code
        dir = fri_station_dir+code
        d=ds
        while d < de:
          day=d.strftime('%Y%m%d')
          # check if the directory exists and contains interesting data
          dir=fri_station_dir+code+'/'
          yyyymmdir=dir+d.strftime('%Y%m')+'/'
          capdir=yyyymmdir+'captures/'
          scamp_ahead_file=fri_station_dir+code+'/metadata/scamp.ahead'
          mask_file=fri_station_dir+code+'/metadata/mask.fits'
          if (os.path.isdir(capdir) and os.path.isfile(scamp_ahead_file) and os.path.isfile(mask_file)):
            # check if the capdir subdirectory is empty or not
            if (os.listdir(capdir)):
               print prog+"now treating station: "+name+" in capdir=",capdir+" for day: "+day
               FriPipe(code,d.strftime('%Y%m%d'),pipeline_process,mask=dir+"/metadata/mask.fits",omask="om",confpath=fri_pipeline_path+"conf/",ahead=dir+"/metadata/scamp.ahead").runprocess()
#            else:
#               print prog+" capdir "+capdir+" is empty..."
#          else:
#            print prog+"directory "+capdir+" does not exist or does not contain interesting data for "+prog+" or scamp file or mask file does not exist"
          d += datetime.timedelta(days=1)

        # end of while d < de:
    # end of for row in reader:
# end of with open(fri_station_file, 'rb') as f: 
print prog+"done"
