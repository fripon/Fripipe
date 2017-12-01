"""Perform one or several fripon pipeline process level(s).

Syntax is: "python processing.py code start end proc_level"

Parameters
----------
code : string
    FRIPON station code
start : string
    start date of the data to consider for the process. Format is yyyymmdd.
end : string
    end date of the data to consider for the process. Format is yyyymmdd.
proc_level : string
    process or processes to launch. If several processes are wanted to be launched, their numbers must be separated by comas. Example: "2,3" will launch successively the processes number 2 and 3.

Returns
-------
None :
    The desired pipeline process/processes are launched.

See Also
--------
Documentation of the fripipe_launch.py module.

This file is part of FriPipe, the FRIPON reduction pipeline
18/05/2016

Author : FRIPON team

Copyright : Observatoire de Paris, Universite Paris-Sud, CNRS, FRIPON

Free licence

"""

from fripipe import fripipe_launch
import sys
import os, glob
import csv
import datetime
from datetime import timedelta
from fripipe.path_and_file import fri_station_file, fri_station_dir, fri_pipeline_path,fri_proc_dir,fri_meta_dir,fri_conf_dir
from fripipe.fripipe_launch import FriPipe
from fripipe.conversion import code2name

prog="(processing.py) "
syntax="python processing.py code start end proc_level"

# setting arguments by default
code="XXXX00"
start=9999
end=9999
arg_process=[0]

# get the arguments
if (len(sys.argv) != 5):       # because sys.argv[0] is the name of the program
    sys.exit(prog+"*** FATAL ERROR: syntax is: "+syntax)
else:
    code=sys.argv[1]
    start=sys.argv[2]
    end=sys.argv[3]
    arg_process=sys.argv[4]
print prog,"========================="
print prog,"= Now processing station code="+code+" from date="+start+" to "+end+" with proc_level="+arg_process
print prog,"========================="

pipeline_process=map(int,arg_process.split(','))

# dates of start and end of processing
day_stt = datetime.datetime.strptime(start, '%Y%m%d')
day_end = datetime.datetime.strptime(end, '%Y%m%d')

# get station code into station name
name = code2name.code2name(code)

dir = fri_station_dir+code+'/'
procdir = fri_proc_dir+code+'/'
metadir = fri_meta_dir+code+'/'
scampdir = procdir+'scamp/'
scamp_ahead_file = scampdir+'scamp.ahead'
mask_file = metadir+'/mask.fits'
procdir = fri_proc_dir+code


# General checks before doing anything
if (os.path.isdir(dir)):
    print prog+"Now treating station "+name
else:
    sys.exit(prog+"*** FATAL ERROR: Directory "+dir+" does not exist")
if not (os.path.isdir(procdir)):
    sys.exit(prog+"*** FATAL ERROR: Directory "+procdir+" does not exist")
if (not os.path.isfile(scamp_ahead_file)):
    sys.exit(prog+"*** FATAL ERROR: scamp_ahead_file "+scamp_ahead_file+" does not exist")
if (not os.path.isfile(mask_file)):
    sys.exit(prog+"*** FATAL ERROR: mask_file "+mask_file+" does not exist")


# end of checks now do the job
if (pipeline_process[0] == 5):
    print prog+'Now launching fripipe_launch with pipeline_process=5'
    pipeline=FriPipe(code,day_stt.strftime('%Y%m%d'),mask=mask_file,omask="om",confpath=fri_conf_dir,ahead=scamp_ahead_file)
    pipeline.runprocess(pipeline_process)
    print prog,'done'
    sys.exit()
else: 
    print prog+'Now launching Fripipe with pipeline_process=',pipeline_process
    day_cur=day_stt
    while day_cur <  day_end:
        # check if the captures directory exists and contains interesting data
        yyyymmdir=dir+'/'+day_cur.strftime('%Y%m')+'/'
        capdir=yyyymmdir+'/' 
        extn = 'fit'
        if (os.path.isdir(capdir)):
            # check if the capdir subdirectory is empty or not
            if (os.listdir(capdir)):
                print prog+"now treating station: "+name+" in capdir=",capdir+" for day: "+day_cur.strftime('%Y%m%d')
                listfile=glob.glob(capdir+'/'+code+'_'+day_cur.strftime('%Y%m%d')+'*.'+extn)
                print prog,'There are ',len(listfile),' files of type ',capdir+'/'+code+'_'+day_cur.strftime('%Y%m%d')+'*.'+extn
                if (len(listfile) != 0):
                    pipeline=FriPipe(code,day_cur.strftime('%Y%m%d'),mask=mask_file,omask="om",confpath=fri_conf_dir,ahead=scamp_ahead_file)
                    pipeline.runprocess(pipeline_process)
                else:
                    print prog,'There is no file of type ',capdir+'/'+code+'_'+day_cur.strftime('%Y%m%d')+'*.'+extn+' to process for day ',day_cur.strftime('%Y%m%d')
            else:
                print prog+"*** Warning: directory "+capdir+" is empty..."
        else:
            print prog+"*** Warning: directory "+capdir +" does not exist"
        day_cur += datetime.timedelta(days=1)
print prog+"done"

