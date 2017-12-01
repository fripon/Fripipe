"""Definition of the differente pipeline processes.

Declaration of the FriPipe Object.

This file is part of FriPipe, the FRIPON reduction pipeline
18/05/2016

Author : FRIPON team

Copyright : Observatoire de Paris, Universite Paris-Sud, CNRS, FRIPON

Free licence

"""

import os
import sys
import fnmatch
import glob
import datetime
import astropy
from astropy.io import fits
import numpy as np
import procstep
import fillimagetable
from fripipe.path_and_file import fri_station_dir,fri_proc_dir,fri_conf_dir

"""
The Pipeline
"""
class FriPipe(object):
    """FRIPON pipeline Object.
    
    Allows to define all the parameters and then to launch a specific process level as:
        
        1 : raw data insertion in database
        
        2 : image processing (median production and subtraction).
        
        3 : astrometry (catalog extraction and selection).
        
        4 : PSF modeling and refined catalog extraction TBD.
        
        5 : global astrometry calibration.
        
        6 : triangulation (choice of the preferred astrometry and application to event, then orbits and trajectory computing) TBD.
        
        7 : outreach products (TBD).
    
    Parameters
    ----------
    stationcode : string
        FRIPON station code for which the pipeline needs to be processed. This also defines where the raw data are to be found and where the processed data are to be stored.
    startnight : string
        Start date of the process. Format is: YYYYMMDD.
    mask : string, optional
        image mask filename, in particular used by SExtractor to extract stars. See also: http://readthedocs.org/projects/sextractor/
    omask : string, optional
        output mask file name from the image processing process level.
    confpath : string, optional
        path to the configuration files location. Default is the fripipe.fri_conf_dir variable
    ahead : string, optional
        SCAMP software ahead file name. See also: http://readthedocs.org/projects/scamp/ 
    
    """
    # FriPipe object initialization #    
    def __init__(self,stationcode,startnight,mask="",omask="",med="",confpath=fri_conf_dir,ahead=""):
        # The human readable station name #
        #self.__station = station
        # The FRIPON station code #
        self.__stationcode = stationcode
        # The starting date of the night to be processed YYYYMMDD #
        self.__startnight = startnight
        # The starting processing level #
        self.__proclevel = 0
        # The input mask for masking non-exposed regions
        self.__mask = mask
        # The output mask prefix for hot and bad pixel
        # masking in catalog extraction
        self.__omask = omask
        # The output slippy median prefix
        self.__med = med 
        # The configuration file path of FriPipe
        self.__confpath = confpath
        # The SCAMP .ahead file
        self.__ahead = ahead

    def runprocess(self,proclevel):
        """Runs a specified process.
        
        Parameters
        ----------
        proclevel : integer
            process id to be processed. For an exhaustive list of possible process id, please refer to the FriPipe Object documentation in the fripipe.fripipe_launch module.
        
        Returns
        -------
        None : 
            The process level proclevel is processed.
        
        See Also
        --------
        For an exhaustive list of possible process id, please refer to the FriPipe Object documentation in the fripipe.fripipe_launch module.
        """
        # The starting processing level #
        self.__proclevel = proclevel
        # Defining variables #
        dstart = datetime.datetime.strptime(self.__startnight, '%Y%m%d')
        mdir = dstart.strftime('%Y%m')+'/'
        inpath = fri_station_dir + "/" + (str(self.__stationcode)).upper() + "/" + mdir
        outpath = fri_proc_dir + "/" + (str(self.__stationcode)).upper() + "/" + mdir
        d = datetime.datetime.strptime(self.__startnight, '%Y%m%d') + datetime.timedelta(days=1)
        
        inpathastro = inpath 
        day = dstart.strftime('%d')
        outpathastro = outpath + "/processed_" + day + "/"
        
        prog="(FriPipe) "
        print prog," =============================="
        print prog," = now launching procelevel ",self.__proclevel, " for station ",self.__stationcode
        print prog," = for date: "+self.__startnight
        print prog," =============================="
        print prog," now putting output into outpathastro="+outpathastro
        """
        proclevel:
        1 : raw data insertion in database
        2 : processing (median production and subtraction)
        3 : astrometry (catalog extraction and selection)
        4 : PSF modeling and refined catalog extraction
        5 : global astrometry calibration
        6 : triangulation (choice of the preferred astrometry and
            application to event, then orbits and trajectory computing)
        7 : outreach products
        """
        proclev = self.__proclevel
        for lev in proclev:
            if lev == 1 :
                print prog,'Filling image table in FRIPON database'
                fillimagetable.fill(inpathastro)
            elif lev == 2 :
                print prog,'Processing (median production and subtraction)'
                if not os.path.isdir(outpathastro):
                    print prog,'now creating outut astrometry directory: ',outpathastro
                    os.mkdir(outpathastro)
                listim=glob.glob(inpathastro+'*.fit')
                print prog,'There are ',len(listim),' images in ',inpathastro
                for im in glob.glob(inpathastro+'*.fit'):
                    print prog,'now considering image: ',im
                    imnight = inpathastro+self.__stationcode+'_'+self.__startnight + '*.fit'
                    imnight2 = inpathastro+self.__stationcode+'_'+str(int(self.__startnight)+1) + '*.fit'
                    if fnmatch.fnmatch(im, imnight) or fnmatch.fnmatch(im, imnight2):
                      if os.path.isfile(im) and os.stat(im).st_size > 0:
                        hdulist = fits.open(im)
                        try:
                            exptime = hdulist[0].header['EXPOSURE']
                        except:
                            print prog,'Cannot find EXPOSURE keyword! Skipping'
                            continue
                        try:
                            dateobs = datetime.datetime.strptime(hdulist[0].header['DATE-OBS'], '%Y-%m-%dT%H:%M:%S.%f' )
                        except:
                            try:
                                dateobs = datetime.datetime.strptime(hdulist[0].header['DATE-OBS'], '%Y-%m-%dT%H:%M:%S' ) 
                            except ValueError:
                                print ValueError
                        hdulist.close()
                        if (exptime == 5.0 and dateobs > d-datetime.timedelta(days=0.5) and dateobs < d+datetime.timedelta(days=0.5)):
                            lnkim=outpathastro+os.path.basename(im)
                            if not os.path.islink(lnkim):
                                print prog+'now creating symbolic link,  from image ',im,' to ',lnkim
                                try:
                                    os.symlink(im,outpathastro+os.path.basename(im))
                                except:
                                    sys.exit(prog+'*** FATAL ERROR: impossible to symlink '+im+' into '+outpathastro)
                print prog,'outpathastro=',outpathastro
                print prog,'mask=',self.__mask
                print prog,'omask=',self.__omask
                print prog,'med=',self.__med
                print prog,'now launching slippymedian'
                procstep.slippymedian(outpathastro,10,mask=self.__mask,omask=self.__omask,med=self.__med)
            elif lev == 3 :
                print(''.join([prog, 'Astrometry (catalog extraction and selection)']))
                procstep.qualitytest(outpathastro,mask=self.__mask,inmask=self.__omask,confpath=self.__confpath,ahead=self.__ahead)
            elif lev == 4 :
                print(''.join([prog, 'PSF modeling and refined cataog extraction']))
            elif lev == 5 :
                print(''.join([prog, 'Global astrometric calibration']))
                scampdir = fri_proc_dir + "/" + (self.__stationcode).upper() + "/"
                procstep.globalastro(scampdir,confpath=self.__confpath,ahead=self.__ahead)
            else:
                print(''.join([prog, 'No corresponding step processing!!']))

