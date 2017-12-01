"""Process a multiple detections event.

The event is located in fripipe.fri_detect_dir directory

Parameters
----------
eventname : string
    name of the event where the data are saved.

Returns
-------
None : 
    The event is being fully processed and results are saved.

Notes
-----
syntax is: python processievent_from_arg.py eventname
the following directories and files HAVE to exist:
    my_detectdir: local directory where the original data will be sym-linked
The following scripts and softwares are launched by this program:
    launch gethead4event.py script to get the best scamp head file and sym-linked it to local directory
    launch sexmet_auto_detect.sh script output [X,Y,RA,DEC] of the event, using scamp output from previous step
    launch position2met.py to create the *.met files
    launch compute_traj_from_arg.py script to compute trajectory and orbit, once the previous steps are done for all stations of the event
"""
from astropy.io.votable import parse
import sys
import datetime
import os
import glob
import numpy as np
from fripipe.path_and_file import data_dir,fri_proc_dir,fri_station_file,fripipe_shell_path,work_detc_dir,work_mult_dir
from fripipe.trajectory import compute_traj
from fripipe.conversion import name2code,code2name
from fripipe.position2met import position2met

#===============================================

def gethead4event(eventname,stationname,mincontrast=5.0,maxdeltat=30.0):
    """get the scamp-generated head file to reduce observations.
    
    Get the scamp-generated head file corresponding to the stationname station,
    having the minimum contrast (see scamp doc) greater or equal than
    mincontrast (=5 by default) and which date is less than maxdeltat days
    (default=30) from the event named eventname.
    
    Parameters
    ----------
    eventname : string
        Name of directory where all the event data is stored.
        example: '20160806T220747_UT'
    stationname : string
        Name of station for which we want the .head file
    mincontrast : float
        minumum contrast (in the scamp sense of the term) required for
        the .head file (see the scamp software doc at: www.astromatic.net).
    maxdeltat: float
        maxim um time difference between the date of the event and that
        of the .head file. Unit is days.
    
    Returns
    -------
    headfile : string
        Full path file name of the .head file (previously created by the scamp
        software, see procstep=5).
    
    """
    prog="(gethead4event.py) "
    
    #print prog,'eventname=',eventname
    #print prog,'stationname=',stationname
    # get the date of the event thanks to the name of the directory
    y=int(eventname[0:4])
    m=int(eventname[4:6])
    d=int(eventname[6:8])
    h=int(eventname[9:11])
    n=int(eventname[11:13])
    s=int(eventname[13:15])
    eventtime=datetime.datetime.strptime(eventname[0:15],'%Y%m%dT%H%M%S')
    eventdecimalyear=(float(y)+float(m)/12.0+float(d)/365.0+
                      float(h)/(365.0*24.0)+float(n)/(365.0*24.0*60.0)+
                      float(s)/(365.0*24.0*60.0*60.0))
    if not os.path.isfile(fri_station_file):
        errmsg=prog+"*** FATAL ERROR: station file "+fri_station_file+" does not exist \n"
        sys.exit(errmsg)
    code=name2code.name2code(stationname)
    if (code==""):
        errmsg=prog+"*** FATAL ERROR: station unknown from station file \n"
        sys.exit(errmsg)
    scampxml=fri_proc_dir+code+"/scamp/scamp.xml"
    if os.path.isfile(scampxml):
        votable = parse(scampxml)
        table = votable.get_first_table()
        contrast = (table.array['XY_Contrast']).data
        catname = (table.array['Catalog_Name']).data
        date = (table.array['Observation_Date']).data
        deltatime=(date-eventdecimalyear)*365
        a = zip(deltatime,contrast,catname)
        a.sort()
        if (len(a)==0):
            errmsg=prog+"*** FATAL ERROR: there is no useful data in "+scampxml+"\n"
            sys.exit(errmsg)
        else:
            while (a[0][1]<mincontrast):
                del a[0]
            return fri_proc_dir+code+"/scamp/"+os.path.splitext(a[0][2])[0]+'.head'
    else:
        errmsg=prog+"*** FATAL ERROR: scamp xml file "+scampxml+" does not exist \n"
        sys.exit(errmsg)

#=================================================
#=================== MAIN ========================
#=================================================
prog="(processevent_from_arg.py) "
syntax="python processevent_from_arg.py eventname"
eventname=sys.argv[1]
print prog,"eventname=",eventname
if not len(eventname):
    sys.exit(prog+"*** FATAL ERROR: please specify the event name. syntax is"+synt)
yyyymm=eventname[:6]
eventdir="/".join([work_mult_dir,yyyymm,eventname])
print prog,"evendir=",eventdir
user=os.environ['USER']
home=os.environ['HOME']
if not (user=="fripon"):
    datadir="/home/"+user+"/"
    userfri=0
else:
    datadir=data_dir
    userfri=1
my_detectdir=datadir+"/detections/multiple/"

fripon_detectdir=datadir+"/detections/multiple"
fits2D_dir="fits2D"
position_file="positions.txt"

# verification
if not os.path.isfile(fri_station_file):
    sys.exit(prog+" ### FATAL ERROR:  fri_station_file: "+fri_station_file+" does not exist")
if not os.path.isdir(fripon_detectdir):
    sys.exit(prog+" #### FATAL ERROR: fripon_detectdir: "+fripon_detectdir+" does not exist")

#=================================================
# loop over the detections
allevents=glob.glob("/".join([work_mult_dir,yyyymm,eventname+"*"]))
if (len(allevents)==0):
    sys.exit(prog+" *** FATAL ERROR: There is no event "+eventname)
else:
    print prog,"List of events to process: ",allevents
for my_event in allevents:
    my_detection_dir=os.path.dirname(my_event)
    my_detection_name=os.path.basename(my_event)
    output_dir=my_event+"/Trajectory"
    output_dir=output_dir.replace(data_dir,datadir)
    print prog+"#########################################"
    print prog+"# Now treating my_event= ",my_event
    print prog+"# my_detection_name=",my_detection_name
    print prog+"#########################################"
    print prog,'datadir=',datadir
    print prog,'data_dir=',data_dir
    print prog,'my_detection_dir=',my_detection_dir
    print prog,'my_detectdir=',my_detectdir
    print prog,'output_dir=',output_dir
    print prog+"#########################################"
    if not os.path.isdir(output_dir):
        print prog+"now creating directory: "+output_dir
        os.makedirs(output_dir)
    # log file
    my_logfile=output_dir+"/processmultidetect.log"
    print prog,'log info will be saved in logfile=',my_logfile
    plzchklog="Please check the log file located in "+my_logfile+" for more info"
    log=open(my_logfile,'w')
    log.write(str(datetime.datetime.now())+"\n")

    # now loops over all the stations and checks that all the needed data are present
    listations=glob.glob(my_event+"/*_UT")
    msg=''.join([prog,'the directory ',my_event,
        ' contains the following usefull directories: ',
        ' '.join(listations),'\n'])
    log.write(msg)
    print msg
    if (len(listations)==0):
        msg=prog+'*** FATAL ERROR: there is no station observation record in '+my_event+'\n'
        log.write(msg)
        sys.exit(msg)
    for station in listations:
        if (station.endswith('_UT')):
            print prog,'station=',station
            name=station.split('/')[-1].split('_' )[0]
            codestn=name2code.name2code(name)
            msg=''.join([prog,"now checking data for station ",name,
                              " (code=",codestn,") \n"])
            log.write(msg)
            print msg
            # First check if the scamp.xml file is present
            scampxmlfile=datadir.replace(datadir,data_dir)+"/stations/"+codestn+"/scamp/scamp.xml"
            if os.path.isfile(scampxmlfile):
                msg=prog+"scamp.xml file exsits for station "+name+" "+ codestn+". ok! \n"
                log.write(msg)
                print msg
            else:
                msg=''.join([prog,"*** FATAL ERROR: file ",scampxmlfile,
                    " does not exist (station=",name,
                    "). Please run processing.py with proclevel=5 for station ",
                    codestn,"\n"])
                log.write(msg)
                sys.exit(msg+plzchklog)
            # now checks that the observation data are all here
            positionfile=station+'/'+position_file
            if not os.path.isfile(positionfile):
                msg=prog+"*** FATAL ERROR: file "+positionfile+" does not exist. Aborting program \n"
                log.write(msg)
                sys.exit(msg+plzchklog)
            else:
                msg=prog+positionfile+" does exist. ok! \n"
                log.write(msg)
                print msg
                # now symlink the data if the user is not fripon
                if not userfri:
                    # first creates the appropriate directory
                    if not os.path.isdir(station.replace(data_dir,datadir)):
                        msg=prog+"now creating directory "+station.replace(data_dir,datadir)+"\n"
                        log.write(msg)
                        print msg
                        os.system("mkdir -p "+station.replace(data_dir,datadir)) # because the following does not work: os.makedirs(station.replace(data_dir,datadir))
                # now creates symbolic link
                if not os.path.islink(positionfile.replace(data_dir,datadir)):
                    msg=prog+"symlink "+positionfile+" into "+positionfile.replace(data_dir,datadir)+"\n"
                    log.write(msg)
                    print msg
                    os.symlink(positionfile,positionfile.replace(data_dir,datadir))
            # now test if the images are present or not
            fits2Ddir=station+"/"+fits2D_dir
            listfits2D=glob.glob(fits2Ddir+"/*")
            msg=''.join([prog,'the directory ',fits2Ddir,
                        ' contains the following files: ',
                        ' '.join(listfits2D),"\n"])
            log.write(msg)
            #print msg
            if (len(listfits2D)==0):
                msg=''.join([prog,"*** FATAL ERROR: directory ",fits2Ddir,
                             " is empty. Aborting program \n"])
                log.write(msg)
                sys.exit(msg+plzchklog)
            else:
                msg=''.join([prog,fits2Ddir," is not empty. ok! \n"])
                log.write(msg)
                print msg
            # now symlynk of user is not fripon
            if not userfri:
                if not os.path.isdir(fits2Ddir.replace(data_dir,datadir)):
                    os.makedirs(fits2Ddir.replace(data_dir,datadir))
                os.chdir(fits2Ddir.replace(data_dir,datadir))
            for fitfile in glob.glob(fits2Ddir+"/*.fit"):
                if not os.path.islink(fitfile.replace(data_dir,datadir)):
                    msg=''.join([prog,"symlink ",fitfile," into ",
                            fitfile.replace(data_dir,datadir),"\n"])
                    log.write(msg)
                    print msg
                    os.symlink(fitfile,fitfile.replace(data_dir,datadir))
            for catafile in glob.glob(fits2Ddir+"/*.cata"):
                if not os.path.islink(catafile.replace(data_dir,datadir)):
                    msg=''.join([prog,"symlink ",catafile," into ",
                            catafile.replace(data_dir,datadir),"\n"])
                    log.write(msg)
                    print msg
                    os.symlink(catafile,catafile.replace(data_dir,datadir))
            for headfile in glob.glob(fits2Ddir+"/frame*.head"):
                if not os.path.islink(headfile.replace(data_dir,datadir)):
                    msg=''.join([prog,"symlink ",headfile," into ",
                            headfile.replace(data_dir,datadir),"\n"])
                    log.write(msg)
                    print msg
                    os.symlink(headfile,headfile.replace(data_dir,datadir))
            os.chdir(station)
    # ==============================
    # Now really process the data
    # loop over the stations
    for station in glob.glob(my_event+"/*"):
        if (station.endswith('_UT')):
            stationame=station.split('/')[-1].split('_' )[0]
            codestn=name2code.name2code(stationame)
            msg=prog+"=== now treating data in "+station+" from station: "+stationame+" (code="+codestn+") \n"
            print "-------------------------"
            log.write(msg)
            print msg
            #=================================================
            # select the scamp *.head file that is the closest in time, and with a good contrast
            # using the path to determine where to look for scamp xml file
            head_file=gethead4event(my_detection_name,stationame)
            print prog,"head_file=",head_file
            if not os.path.isfile(head_file): 
                msg=prog+"*** FATAL ERROR: head_file="+head_file+" not created for some reasons... \n"
                log.write(msg)
                sys.exit(msg+plzchklog)
            # copy the best *.head file into the fits2D directory but remove the CRVAL lines
            fits2Ddir=station+"/"+fits2D_dir
            local_file="/".join([fits2Ddir,"head.head"])
            if not userfri:
                local_file=local_file.replace(data_dir,datadir)
            if os.path.isfile(local_file):
                os.remove(local_file)
            cmd="grep -v CRVAL "+head_file+" > "+local_file
            msg=prog+"now launching cmd="+cmd+"\n"
            log.write(msg)
            print msg
            os.system(cmd)
            if not os.path.isfile(local_file):
                msg=prog+"*** FATAL ERROR: best *.head file could not be copied into "+local_file+" for some reasons \n"
                log.write(msg)
                sys.exit(msg)
            msg=prog+head_file+" copied into "+local_file+" and CRVAL removed ok \n"
            log.write(msg)
            print msg
            #=================================================
            # launches sextractor with the good options, again using the path to get the mask file
            msg=prog+"now relocating to "+fits2Ddir.replace(data_dir,datadir)+"\n"
            log.write(msg)
            print msg
            os.chdir(fits2Ddir.replace(data_dir,datadir))
            # first check if the cata files are already here => useless to run sextractor again (takes a lot of time...)
            listcata=glob.glob("*.cata")
            listfit=glob.glob("*.fit")
            listhead=glob.glob("*.head")
            msg=prog+"number of fit, cata and head files="+str(len(listfit))+" "+str(len(listcata))+" "+str(len(listhead))+"\n"
            log.write(msg)
            print msg
            if not (len(listfit)==len(listcata) and (len(listfit)==len(listhead)-1)):
                cmd=fripipe_shell_path+"/sexmet_auto_detect.sh "+stationame
                msg=prog+"now launching cmd="+cmd+"\n"
                log.write(msg)
                print msg
                os.system(cmd)
            # now checks the result of the sexmet_auto_detect.sh script
            # ADD HERE A WAY TO DOUBLE CHECK THAT THE PREVIOUS STEP IS OK
            #=================================================
            # launches the position2met.sh script
            msg=prog+"now relocating to "+station.replace(data_dir,datadir)+"\n"
            log.write(msg)
            print msg
            os.chdir(station.replace(data_dir,datadir))
            log.write(msg)
            print msg
            met_file = station.split('/')[-1]+'.met'
            msg=prog+"now launching the position2met process. Data will be saved in met_file="+met_file
            log.write(msg)
            print msg
            position2met(position_file,fits2D_dir,met_file)
    # end of loop over the stations
    #=================================================

    # launches the computation of orbits
    msg=''.join([prog,"-------------------------------- \n",
                 prog,"now launches the computation of trajectory and orbit for event in ",
                 my_detection_dir,"\n"])
    log.write(msg)
    print msg
    compute_traj.compute_traj(eventname)
    
    msg=''.join([prog,"-------------------------------- \n",
                 prog,"Treatment of event ",my_event," done \n"])
    log.write(msg)
    print msg



msg=prog+'done'
log.write(msg)
print msg

