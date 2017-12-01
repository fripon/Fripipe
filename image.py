"""Definition of Image object.

This file is part of FriPipe, the FRIPON reduction pipeline
18/05/2016

Author : FRIPON team

Copyright : Observatoire de Paris, Universite Paris-Sud, CNRS, FRIPON

Free licence

"""

import os
import os.path
import astropy
from astropy.io import fits
import numpy as np
import numpy.ma as ma
from fripipe import sex_exe, scamp_exe

"""
The Image
"""
class Image(object):
    """Image object, especially used in fripipe.procstep module.
    
    Parameters
    ----------
    imname : string
        image file name
    mask : string, optional
        image mask file name. This is useful for the sextraction method.
    
    """
    # Image object initialization #
    def __init__(self,imname,mask=""):
        self.prog = '(Image.'
        self.__name = imname
        if os.path.isfile(imname):
            hdulist = fits.open(imname)
            self.__header = hdulist[0].header
            self.__data = hdulist[0].data
            hdulist.close()
        else:
            self.__data = 0
            hdu = fits.PrimaryHDU(self.__data)
            self.__header = hdu.header
        if mask != "":
            if os.path.isfile(mask):
                hdulist = fits.open(mask)
                self.__mask = hdulist[0].data
                hdulist.close()
            else:
                print ("WARNING: Cannot open " + mask + ", no mask used.")
        self.__median = 0
        self.__std = 0
    
    def medcomp(self):
        """Image self median computation.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None :
            The self median is computed.
        
        """
        if hasattr(self, '_Image__mask'):
            imarray = ma.array(self.__data, mask=(self.__mask == 0))
            self.__median = np.ma.median(imarray)
        else:
            self.__median = np.median(self.__data)
    
    def mednorm(self):
        """Image self median normalization.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None :
            The self median is normalized.
        
        """
        self.medcomp()
        if self.__median != 0:
            self.__data = self.__data / self.__median
    
    def stdcomp(self):
        """Image self std deviation computation.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None :
            The self std deviation is computed.
        
        """
        if hasattr(self, '_Image__mask'):
            imarray = ma.array(self.__data, mask=(self.__mask == 0))
        else:
            imarray = self.__data
        self.__std = np.std(imarray)
    
    def sextraction(self, confpath="", conf="", options=""):
        """Sextracting Image.
        
        The SExtractor software (see: www.astromatic.net/software/sextractor) is applied to the image in order to extract the sources.
        
        Parameters
        ----------
        confpath : string, optional
            configuration path name where the SExtractor configuration files are located.
        conf : string, optional
            SExtractor configuration file name.
        options : string, optional
            SExtractor options to be passed in the command line.
        
        Returns
        -------
        None :
            The SExtractor software is executed.
        
        See Also
        --------
        http://readthedocs.org/projects/sextractor/
        
        """
        prog = self.prog+'sextraction) '
        ex = sex_exe
        if conf != "":
            conf = "-c " + conf
        if confpath != "":
            options = options + " -PARAMETERS_NAME " + confpath + "/sextractor/default.param"
            options = options + " -FILTER_NAME " + confpath + "/sextractor/default.conv"
            options = options + " -STARNNW_NAME " + confpath + "/sextractor/default.nnw"
        cmd = ex + self.__name + " " + conf + " " + options
        print prog+"*** now launching sextractor with the command:"
        print cmd
        os.system(cmd)
        
    def scamption(self, confpath="", conf="", ahead="", options=""):
        """Scamping Image.
        
        The SCAMP software (see: www.astromatic.net/software/scsamp) is applied to output of the SExtractor process.
        The goal is to perform the astrometry calibration of the image.
        
        Parameters
        ----------
        confpath : string, optional
            configuration path name where the SCAMP configuration files are located.
        conf : string, optional
            SCAMP configuration file name.
        ahead : string, optional
            SCAMP global header file name ; see also: http://readthedocs.org/projects/scamp/
        options : string, optional
            SExtractor options to be passed in the command line.
        
        Returns
        -------
        None :
            The SCAMP software is executed.
        
        See Also
        --------
        http://readthedocs.org/projects/scamp/
        
        """
        prog = self.prog+'scamption) '
        ex = scamp_exe
        if conf != "":
             conf = "-c " + conf
        if confpath != "":
             conf = "-c " + confpath + "/scamp/scamp.conf"
        if ahead != "":
             options = options + " -AHEADER_GLOBAL  " + ahead
        cmd = ex+self.__name + ".ldac " + conf + " " + options
        print prog,"*** now launching scamp with the command:"
        print cmd
        os.system(cmd)

    # Saving new Image #
    def save(self):
        """Save the Image.
        
        Overwirtten option is set to True.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None :
            The image is saved.
        
        """
        if hasattr(self, '_Image__mask'):
            mimarray = ma.array(self.__data, mask=(self.__mask == 0))
            imarray = mimarray.data
        else:
            imarray = self.__data
        self.__data = imarray
        hdu = fits.PrimaryHDU(self.__data,header=self.__header)
        print '(Image.save) now saving image into ',self.__name
        hdu.writeto(self.__name,overwrite=True)
